from matplotlib.figure import Figure
import io
import networkx as nx
import objc
from Cocoa import NSObject, NSMakeRect, NSData
from AppKit import NSView, NSImageView
from AppKit import NSViewWidthSizable, NSViewHeightSizable
import database
import matplotlib
matplotlib.use("Agg")


class GraphPage(NSObject):
    def init(self):
        self = objc.super(GraphPage, self).init()
        if self is None:
            return None
        content_rect = NSMakeRect(0, 0, 1000, 620)
        self.view = NSView.alloc().initWithFrame_(content_rect)
        self.view.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable)
        # Draw initial graph (if any data)
        self.refresh()
        return self

    def refresh(self):
        # Remove previous graph image if exists
        if hasattr(self, "img_view") and self.img_view:
            self.img_view.removeFromSuperview()
            self.img_view = None
        # If no period selected, do nothing
        if not database.current_period:
            return
        # Build model graph data for current period
        con = database.get_connection()
        cur = con.cursor()
        period = database.current_period
        # Resource costs
        cur.execute("SELECT r.id, r.name, COALESCE(rc.cost, r.cost_total) FROM resources r LEFT JOIN resource_costs rc ON r.id = rc.resource_id AND rc.period=?", (period,))
        resource_data = {row[0]: {"name": row[1], "cost": row[2]}
                         for row in cur.fetchall()}
        # Resource->Activity allocations
        cur.execute(
            "SELECT resource_id, activity_id, amount FROM resource_allocations_monthly WHERE period=?", (period,))
        res_alloc = {}
        total_by_res = {}
        for r_id, a_id, amount in cur.fetchall():
            res_alloc.setdefault(r_id, {})[a_id] = amount
            total_by_res[r_id] = total_by_res.get(r_id, 0) + amount
        activity_costs = {}
        resource_to_activity = {}
        for r_id, allocs in res_alloc.items():
            total_amt = total_by_res.get(r_id, 0)
            if total_amt == 0 or r_id not in resource_data:
                continue
            for a_id, amt in allocs.items():
                share = amt / total_amt
                cost_contrib = resource_data[r_id]["cost"] * share
                activity_costs[a_id] = activity_costs.get(
                    a_id, 0) + cost_contrib
                resource_to_activity[(r_id, a_id)] = cost_contrib
        # Activity->CostObject allocations
        cur.execute("SELECT aa.activity_id, aa.cost_object_id, aa.quantity, aa.driver_value_id, a.evenly, dv.value FROM activity_allocations_monthly aa JOIN activities a ON a.id = aa.activity_id LEFT JOIN driver_values dv ON dv.id = aa.driver_value_id WHERE aa.period=?", (period,))
        act_alloc = {}
        total_by_act = {}
        for a_id, c_id, qty, drv_id, evenly, drv_val in cur.fetchall():
            if evenly == 1:
                eff_qty = 1.0
            elif drv_id is not None and drv_val is not None:
                eff_qty = drv_val
            else:
                eff_qty = qty
            act_alloc.setdefault(a_id, {})[c_id] = eff_qty
            total_by_act[a_id] = total_by_act.get(a_id, 0) + eff_qty
        cost_object_totals = {}
        activity_to_costobj = {}
        for a_id, cost in activity_costs.items():
            total_qty = total_by_act.get(a_id, 0)
            if total_qty == 0:
                # Activity has no allocations to cost objects (unallocated cost)
                continue
            for c_id, qty in act_alloc.get(a_id, {}).items():
                share = qty / total_qty
                value = cost * share
                cost_object_totals[c_id] = cost_object_totals.get(
                    c_id, 0) + value
                activity_to_costobj[(a_id, c_id)] = value
        # If no activities have cost, nothing to draw
        if not activity_costs:
            con.close()
            return
        # Fetch names for activities and cost objects
        cur.execute("SELECT id, name FROM activities")
        all_activities = {row[0]: row[1] for row in cur.fetchall()}
        cur.execute("SELECT id, name FROM cost_objects")
        all_costobjs = {row[0]: row[1] for row in cur.fetchall()}
        con.close()

        # Build graph nodes and edges (using networkx)
        G = nx.Graph()
        node_labels = {}
        node_colors = []
        edge_labels = {}

        # Add Resource nodes (prefix "R")
        for r_id, data in resource_data.items():
            if data["cost"] is None:
                continue
            node = f"R{r_id}"
            G.add_node(node)
            node_labels[node] = f"R: {data['name']}\n{data['cost']:.2f}"
            node_colors.append("#FF6666")  # red for resources

        # Add Activity nodes (prefix "A")
        for a_id, cost in activity_costs.items():
            node = f"A{a_id}"
            G.add_node(node)
            name = all_activities.get(a_id, str(a_id))
            node_labels[node] = f"A: {name}\n{cost:.2f}"
            node_colors.append("#FFCC33")  # orange for activities

        # Add Cost Object nodes (prefix "O")
        for c_id, total in cost_object_totals.items():
            node = f"O{c_id}"
            G.add_node(node)
            name = all_costobjs.get(c_id, str(c_id))
            node_labels[node] = f"O: {name}\n{total:.2f}"
            node_colors.append("#99CC66")  # green for cost objects

        # Add edges Resource→Activity
        for (r_id, a_id), value in resource_to_activity.items():
            res_node = f"R{r_id}"
            act_node = f"A{a_id}"
            if G.has_node(res_node) and G.has_node(act_node):
                G.add_edge(res_node, act_node)
                edge_labels[(res_node, act_node)] = f"{value:.2f}"

        # Add edges Activity→CostObject
        for (a_id, c_id), value in activity_to_costobj.items():
            act_node = f"A{a_id}"
            co_node = f"O{c_id}"
            if G.has_node(act_node) and G.has_node(co_node):
                G.add_edge(act_node, co_node)
                edge_labels[(act_node, co_node)] = f"{value:.2f}"

        # If no activities have cost (graph is empty), nothing to draw
        if not activity_costs:
            con.close()
            return

        con.close()

        # ---- New layered layout: three columns (Resources, Activities, CostObjects) ----
        pos = {}
        # Get sorted lists of nodes by type
        R_nodes = sorted(
            [n for n in G.nodes if n.startswith("R")], key=lambda x: int(x[1:]))
        A_nodes = sorted(
            [n for n in G.nodes if n.startswith("A")], key=lambda x: int(x[1:]))
        O_nodes = sorted(
            [n for n in G.nodes if n.startswith("O")], key=lambda x: int(x[1:]))
        nR, nA, nO = len(R_nodes), len(A_nodes), len(O_nodes)
        # Assign X positions for layers: 0.1 (left), 0.5 (middle), 0.9 (right)
        for i, node in enumerate(R_nodes):
            # Evenly spaced Y positions (top=1.0, bottom=0.0)
            y = 1 - ((i + 1) / (nR + 1)) if nR > 0 else 0.5
            pos[node] = (0.1, y)
        for i, node in enumerate(A_nodes):
            y = 1 - ((i + 1) / (nA + 1)) if nA > 0 else 0.5
            pos[node] = (0.5, y)
        for i, node in enumerate(O_nodes):
            y = 1 - ((i + 1) / (nO + 1)) if nO > 0 else 0.5
            pos[node] = (0.9, y)

        # Draw the graph using Matplotlib
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        nx.draw(G, pos, ax=ax, labels=node_labels, node_color=node_colors,
                with_labels=True, arrows=False, font_size=9)
        nx.draw_networkx_edge_labels(
            G, pos, ax=ax, edge_labels=edge_labels, font_size=8)

        # Convert plot to NSImage for display in the UI
        buf = io.BytesIO()
        fig.savefig(buf, format="png")
        img_data = buf.getvalue()
        nsdata = NSData.dataWithBytes_length_(img_data, len(img_data))
        image = objc.lookUpClass("NSImage").alloc(
        ).initWithData_(nsdata) if nsdata else None
        if not image:
            return
        self.img_view = NSImageView.alloc().initWithFrame_(
            NSMakeRect(0, 0, self.view.frame().size.width, 620))
        self.img_view.setImage_(image)
        try:
            from AppKit import NSImageScaleProportionallyUpOrDown
            self.img_view.setImageScaling_(NSImageScaleProportionallyUpOrDown)
        except Exception:
            pass
        self.img_view.setAutoresizingMask_(
            NSViewWidthSizable | NSViewHeightSizable)
        self.view.addSubview_(self.img_view)
