def calculate_costs(conn):
    """Возвращает (total_by_object, breakdown) где
    total_by_object: {cost_object_id: value}
    breakdown: {cost_object_id: {activity_id: value}}
    """
    cur = conn.cursor()

    # Шаг 1 – стоимость активностей
    cur.execute("SELECT id, cost_total FROM resources")
    resources = {row[0]: row[1] for row in cur.fetchall()}

    cur.execute(
        "SELECT resource_id, activity_id, amount FROM resource_allocations")
    res_alloc = {}
    total_by_resource = {}
    for r_id, a_id, amount in cur.fetchall():
        res_alloc.setdefault(r_id, {})[a_id] = amount
        total_by_resource[r_id] = total_by_resource.get(r_id, 0) + amount

    activity_costs = {}
    for r_id, a_map in res_alloc.items():
        total_amt = total_by_resource[r_id]
        if total_amt == 0:
            continue
        for a_id, amt in a_map.items():
            share = amt / total_amt
            activity_costs[a_id] = activity_costs.get(
                a_id, 0) + resources[r_id] * share

    # Шаг 2 – стоимость объектов затрат
    cur.execute(
        "SELECT activity_id, cost_object_id, quantity FROM activity_allocations")
    act_alloc = {}
    total_by_activity = {}
    for a_id, c_id, qty in cur.fetchall():
        act_alloc.setdefault(a_id, {})[c_id] = qty
        total_by_activity[a_id] = total_by_activity.get(a_id, 0) + qty

    cost_object_totals = {}
    breakdown = {}
    for a_id, cost in activity_costs.items():
        total_qty = total_by_activity.get(a_id, 0)
        if total_qty == 0:
            continue
        for c_id, qty in act_alloc.get(a_id, {}).items():
            share = qty / total_qty
            value = cost * share
            cost_object_totals[c_id] = cost_object_totals.get(c_id, 0) + value
            breakdown.setdefault(c_id, {})[a_id] = value

    return cost_object_totals, breakdown
