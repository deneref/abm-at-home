import os
import pandas as pd
import pytest
import database

DB = database.DB_NAME


def setup_module(module):
    # ensure fresh DB
    if os.path.exists(DB):
        os.remove(DB)
    database.init_db()
    database.reset_all_tables()

    # build minimal excel model
    file_path = os.path.join(os.path.dirname(database.__file__), "model_new.xlsx")
    df_resources = pd.DataFrame([
        {"id": 1, "name": "R1", "cost_total": 100, "unit": "u"}
    ])
    df_activities = pd.DataFrame([
        {"id": 1, "business_procces": "bp1", "activity": "act1", "driver": "drv1", "evenly": 0}
    ])
    df_costobj = pd.DataFrame([
        {"id": 1, "product": "p1", "business_procces": "bp1"},
        {"id": 2, "product": "p2", "business_procces": "bp1"}
    ])
    df_drivers = pd.DataFrame([
        {"id": 1, "name": "drv1"}
    ])
    df_driver_vals = pd.DataFrame([
        {"id": 1, "driver": "drv1", "product": "p1", "value": 2},
        {"id": 2, "driver": "drv1", "product": "p2", "value": 1}
    ])
    df_res_alloc = pd.DataFrame([
        {"resource_id": 1, "activity_id": 1, "amount": 1}
    ])
    df_act_alloc = pd.DataFrame(columns=["activity_id", "cost_object_id", "business_procces", "activity", "product", "cost_object_bp", "driver_value", "driver_amt"])
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df_resources.to_excel(writer, sheet_name="Resources", index=False)
        df_activities.to_excel(writer, sheet_name="Activities", index=False)
        df_costobj.to_excel(writer, sheet_name="CostObjects", index=False)
        df_drivers.to_excel(writer, sheet_name="Drivers", index=False)
        df_driver_vals.to_excel(writer, sheet_name="DriverValues", index=False)
        df_res_alloc.to_excel(writer, sheet_name="ResourceAllocations", index=False)
        df_act_alloc.to_excel(writer, sheet_name="ActivityAllocations", index=False)

    # run insertion
    database.insert_data()


def teardown_module(module):
    file_path = os.path.join(os.path.dirname(database.__file__), "model_new.xlsx")
    if os.path.exists(file_path):
        os.remove(file_path)


def test_costs_after_insert():
    con = database.get_connection()
    cur = con.cursor()
    # activity cost
    cur.execute("SELECT allocated_cost FROM activities WHERE id=1")
    act_cost = cur.fetchone()[0]
    assert act_cost == 100
    # activity allocations created
    cur.execute("SELECT driver_amt, allocated_cost FROM activity_allocations ORDER BY cost_object_id")
    rows = cur.fetchall()
    assert len(rows) == 2
    assert rows[0][0] == 2
    assert rows[1][0] == 1
    assert rows[0][1] == pytest.approx(act_cost * 2 / 3)
    assert rows[1][1] == pytest.approx(act_cost * 1 / 3)
    # cost object costs
    cur.execute("SELECT allocated_cost FROM cost_objects ORDER BY id")
    co_costs = [r[0] for r in cur.fetchall()]
    con.close()
    assert co_costs[0] == pytest.approx(act_cost * 2 / 3)
    assert co_costs[1] == pytest.approx(act_cost * 1 / 3)
