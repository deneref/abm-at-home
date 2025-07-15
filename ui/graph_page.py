from matplotlib.figure import Figure
import io
import objc
from Cocoa import NSObject, NSMakeRect, NSData
from AppKit import NSView, NSImageView, NSButton
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

        btn = NSButton.alloc().initWithFrame_(NSMakeRect(10, 580, 120, 30))
        btn.setTitle_("Show Graph")
        btn.setTarget_(self)
        btn.setAction_("showGraph:")
        self.view.addSubview_(btn)

        # Draw initial graph (if any data)
        self.refresh()
        return self

    def showGraph_(self, sender):
        self.refresh()

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

        # Build nodes and edges manually
        node_labels = {}
        node_colors = {}
        edges = []

        for r_id, data in resource_data.items():
            if data["cost"] is None:
                continue
            node = f"R{r_id}"
            node_labels[node] = f"R: {data['name']}\n{data['cost']:.2f}"
            node_colors[node] = "#FF6666"

        for a_id, cost in activity_costs.items():
            node = f"A{a_id}"
            name = all_activities.get(a_id, str(a_id))
            node_labels[node] = f"A: {name}\n{cost:.2f}"
            node_colors[node] = "#FFCC33"

        for c_id, total in cost_object_totals.items():
            node = f"O{c_id}"
            name = all_costobjs.get(c_id, str(c_id))
            node_labels[node] = f"O: {name}\n{total:.2f}"
            node_colors[node] = "#99CC66"

        for (r_id, a_id), value in resource_to_activity.items():
            edges.append((f"R{r_id}", f"A{a_id}", value))

        for (a_id, c_id), value in activity_to_costobj.items():
            edges.append((f"A{a_id}", f"O{c_id}", value))

        if not activity_costs:
            con.close()
            return

        con.close()

        # Layout positions
        pos = {}
        R_nodes = sorted([n for n in node_labels if n.startswith("R")], key=lambda x: int(x[1:]))
        A_nodes = sorted([n for n in node_labels if n.startswith("A")], key=lambda x: int(x[1:]))
        O_nodes = sorted([n for n in node_labels if n.startswith("O")], key=lambda x: int(x[1:]))
        nR, nA, nO = len(R_nodes), len(A_nodes), len(O_nodes)
        for i, node in enumerate(R_nodes):
            y = 1 - ((i + 1) / (nR + 1)) if nR > 0 else 0.5
            pos[node] = (0.1, y)
        for i, node in enumerate(A_nodes):
            y = 1 - ((i + 1) / (nA + 1)) if nA > 0 else 0.5
            pos[node] = (0.5, y)
        for i, node in enumerate(O_nodes):
            y = 1 - ((i + 1) / (nO + 1)) if nO > 0 else 0.5
            pos[node] = (0.9, y)

        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        ax.axis("off")

        for node, (x, y) in pos.items():
            ax.scatter(x, y, s=800, color=node_colors.get(node, "#cccccc"), edgecolors="black", zorder=2)
            ax.text(x, y, node_labels[node], ha="center", va="center", fontsize=9, zorder=3)

        for n1, n2, val in edges:
            x1, y1 = pos.get(n1, (0, 0))
            x2, y2 = pos.get(n2, (0, 0))
            ax.plot([x1, x2], [y1, y2], color="gray", zorder=1)
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, f"{val:.2f}", fontsize=8, ha="center", va="center")

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
