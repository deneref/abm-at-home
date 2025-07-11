import database


def calculate_costs(conn, period=None):
    """Возвращает (total_by_object, breakdown) для выбранного периода.
    total_by_object: {cost_object_id: value}
    breakdown: {cost_object_id: {activity_id: value}}
    """
    cur = conn.cursor()
    # Determine period to use
    period_code = period if period is not None else database.current_period

    if period_code:
        # Step 1 – calculate activity costs for the selected period
        cur.execute(
            "SELECT r.id, COALESCE(rc.cost, r.cost_total) AS cost "
            "FROM resources r LEFT JOIN resource_costs rc "
            "ON r.id = rc.resource_id AND rc.period=?", (period_code,))
        resources = {row[0]: row[1] for row in cur.fetchall()}
        cur.execute(
            "SELECT resource_id, activity_id, amount FROM resource_allocations_monthly "
            "WHERE period=?", (period_code,))
        res_alloc = {}
        total_by_resource = {}
        for r_id, a_id, amount in cur.fetchall():
            res_alloc.setdefault(r_id, {})[a_id] = amount
            total_by_resource[r_id] = total_by_resource.get(r_id, 0) + amount

        activity_costs = {}
        for r_id, a_map in res_alloc.items():
            total_amt = total_by_resource.get(r_id, 0)
            if total_amt == 0:
                continue
            for a_id, amt in a_map.items():
                share = amt / total_amt
                activity_costs[a_id] = activity_costs.get(
                    a_id, 0) + resources[r_id] * share

        # Step 2 – calculate cost object totals for the period
        cur.execute(
            "SELECT aa.activity_id, aa.cost_object_id, aa.quantity, aa.driver_value_id, a.evenly, dv.value "
            "FROM activity_allocations_monthly aa "
            "JOIN activities a ON a.id = aa.activity_id "
            "LEFT JOIN driver_values dv ON dv.id = aa.driver_value_id "
            "WHERE aa.period=?", (period_code,))
        act_alloc = {}
        total_by_activity = {}
        for a_id, c_id, qty, drv_id, evenly, drv_val in cur.fetchall():
            # Determine effective quantity based on driver/evenly
            if evenly == 1:
                eff_qty = 1.0
            elif drv_id is not None and drv_val is not None:
                eff_qty = drv_val
            else:
                eff_qty = qty
            act_alloc.setdefault(a_id, {})[c_id] = eff_qty
            total_by_activity[a_id] = total_by_activity.get(a_id, 0) + eff_qty

        cost_object_totals = {}
        breakdown = {}
        for a_id, cost in activity_costs.items():
            total_qty = total_by_activity.get(a_id, 0)
            if total_qty == 0:
                continue
            for c_id, qty in act_alloc.get(a_id, {}).items():
                share = qty / total_qty
                value = cost * share
                cost_object_totals[c_id] = cost_object_totals.get(
                    c_id, 0) + value
                breakdown.setdefault(c_id, {})[a_id] = value
        return cost_object_totals, breakdown

    # If no period specified or set, fallback to original calculation over all data
    # (treat as aggregate of all data if current_period is not set)
    # Шаг 1 – стоимость активностей (без учета периодов)
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

    # Шаг 2 – стоимость объектов затрат (без учета периодов)
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
