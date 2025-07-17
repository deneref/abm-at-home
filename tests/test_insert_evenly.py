import os
import pandas as pd
import pytest
import database

DB = database.DB_NAME


def setup_module(module):
    if os.path.exists(DB):
        os.remove(DB)
    database.init_db()
    database.reset_all_tables()

    file_path = os.path.join(os.path.dirname(database.__file__), "model_new.xlsx")

    df_resources = pd.DataFrame([
        {"id": 1, "name": "R1", "cost_total": 80, "unit": "u"}
    ])
    df_activities = pd.DataFrame([
        {"id": 1, "business_procces": "bp1", "activity": "act1", "driver": "", "evenly": 1}
    ])
    df_costobj = pd.DataFrame([
        {"id": 1, "product": "p1", "business_procces": "bp1"},
        {"id": 2, "product": "p2", "business_procces": "bp2"}
    ])
    df_drivers = pd.DataFrame(columns=["id", "name"])
    df_driver_vals = pd.DataFrame(columns=["id", "driver", "product", "value"])
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

    database.insert_data()


def teardown_module(module):
    file_path = os.path.join(os.path.dirname(database.__file__), "model_new.xlsx")
    if os.path.exists(file_path):
        os.remove(file_path)


def test_evenly_allocations_created():
    con = database.get_connection()
    cur = con.cursor()
    cur.execute("SELECT driver_amt FROM activity_allocations ORDER BY cost_object_id")
    rows = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT allocated_cost FROM activities WHERE id=1")
    act_cost = cur.fetchone()[0]
    cur.execute("SELECT allocated_cost FROM cost_objects ORDER BY id")
    co_costs = [r[0] for r in cur.fetchall()]
    con.close()
    assert rows == [1, 1]
    assert act_cost == 80
    assert co_costs[0] == pytest.approx(40)
    assert co_costs[1] == pytest.approx(40)

