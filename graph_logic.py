import database


def build_graph_data(product: str, bproc: str | None = None):
    if not database.current_period:
        return {}, {}, []
    con = database.get_connection()
    cur = con.cursor()
    period = database.current_period
    cur.execute(
        "SELECT r.id, r.name, COALESCE(rc.cost, r.cost_total)"
        " FROM resources r LEFT JOIN resource_costs rc"
        " ON r.id = rc.resource_id AND rc.period=?",
        (period,),
    )
    resource_data = {row[0]: {"name": row[1], "cost": row[2]} for row in cur.fetchall()}

    cur.execute("SELECT resource_id, activity_id, amount FROM resource_allocations")
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
            activity_costs[a_id] = activity_costs.get(a_id, 0) + cost_contrib
            resource_to_activity[(r_id, a_id)] = cost_contrib

    cur.execute("SELECT activity_id, cost_object_id, driver_amt FROM activity_allocations")
    act_alloc = {}
    total_by_act = {}
    for a_id, c_id, amt in cur.fetchall():
        act_alloc.setdefault(a_id, {})[c_id] = amt
        total_by_act[a_id] = total_by_act.get(a_id, 0) + amt

    cost_object_totals = {}
    activity_to_costobj = {}
    for a_id, cost in activity_costs.items():
        total_qty = total_by_act.get(a_id, 0)
        if total_qty == 0:
            continue
        for c_id, qty in act_alloc.get(a_id, {}).items():
            share = qty / total_qty
            value = cost * share
            cost_object_totals[c_id] = cost_object_totals.get(c_id, 0) + value
            activity_to_costobj[(a_id, c_id)] = value

    cur.execute("SELECT id, business_procces || ' X ' || activity AS name FROM activities")
    all_activities = {row[0]: row[1] for row in cur.fetchall()}
    cur.execute("SELECT id, product, business_procces FROM cost_objects")
    cost_obj_rows = cur.fetchall()
    con.close()

    selected_cos = [row[0] for row in cost_obj_rows if row[1] == product and (bproc is None or row[2] == bproc)]
    selected_cos = set(selected_cos)
    if not selected_cos:
        return {}, {}, []

    node_labels = {}
    node_colors = {}
    edges = []

    for (a_id, c_id), value in activity_to_costobj.items():
        if c_id not in selected_cos:
            continue
        edges.append((f"A{a_id}", f"O{c_id}", value))

    keep_activities = {int(e[0][1:]) for e in edges}

    for (r_id, a_id), value in resource_to_activity.items():
        if a_id in keep_activities:
            edges.append((f"R{r_id}", f"A{a_id}", value))

    keep_resources = {int(e[0][1:]) for e in edges if e[0].startswith("R")}

    for r_id in keep_resources:
        data = resource_data.get(r_id)
        if data and data["cost"] is not None:
            node_labels[f"R{r_id}"] = f"R: {data['name']}\n{data['cost']:.2f}"
            node_colors[f"R{r_id}"] = "#FF6667"

    for a_id in keep_activities:
        name = all_activities.get(a_id, str(a_id))
        cost = activity_costs.get(a_id, 0)
        node_labels[f"A{a_id}"] = f"A: {name}\n{cost:.2f}"
        node_colors[f"A{a_id}"] = "#FFCC33"

    for c_id in selected_cos:
        total = cost_object_totals.get(c_id, 0)
        for row in cost_obj_rows:
            if row[0] == c_id:
                name = f"{row[1]} X {row[2]}"
                break
        else:
            name = str(c_id)
        node_labels[f"O{c_id}"] = f"O: {name}\n{total:.2f}"
        node_colors[f"O{c_id}"] = "#99CC66"

    return node_labels, node_colors, edges
