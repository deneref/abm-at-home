import os
import pandas as pd
import database

DB = database.DB_NAME


def setup_module(module):
    if os.path.exists(DB):
        os.remove(DB)
    database.init_db()
    database.reset_all_tables()


def test_sales_roundtrip(tmp_path):
    file_path = tmp_path / "model.xlsx"
    df_resources = pd.DataFrame([{"id": 1, "name": "R", "cost_total": 10, "unit": "u"}])
    df_activities = pd.DataFrame(
        [
            {
                "id": 1,
                "business_procces": "bp",
                "activity": "a",
                "driver": "",
                "evenly": 0,
            }
        ]
    )
    df_costobj = pd.DataFrame([{"id": 1, "product": "p", "business_procces": "bp"}])
    df_drivers = pd.DataFrame(columns=["id", "name"])
    df_driver_vals = pd.DataFrame(columns=["id", "driver", "product", "value"])
    df_res_alloc = pd.DataFrame([{"resource_id": 1, "activity_id": 1, "amount": 1}])
    df_act_alloc = pd.DataFrame(
        columns=[
            "activity_id",
            "cost_object_id",
            "business_procces",
            "activity",
            "product",
            "cost_object_bp",
            "driver_value",
            "driver_amt",
        ]
    )
    df_sales = pd.DataFrame(
        [
            {
                "id": 1,
                "date": "2025-01-01",
                "channel": "online",
                "product": "p",
                "cost_amt": 5,
            },
            {
                "id": 2,
                "date": "2025-01-02",
                "channel": "retail",
                "product": "p",
                "cost_amt": 7,
            },
        ]
    )
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df_resources.to_excel(writer, sheet_name="Resources", index=False)
        df_activities.to_excel(writer, sheet_name="Activities", index=False)
        df_costobj.to_excel(writer, sheet_name="CostObjects", index=False)
        df_drivers.to_excel(writer, sheet_name="Drivers", index=False)
        df_driver_vals.to_excel(writer, sheet_name="DriverValues", index=False)
        df_res_alloc.to_excel(writer, sheet_name="ResourceAllocations", index=False)
        df_act_alloc.to_excel(writer, sheet_name="ActivityAllocations", index=False)
        df_sales.to_excel(writer, sheet_name="Sales", index=False)

    database.import_from_excel(str(file_path))
    con = database.get_connection()
    cur = con.cursor()
    cur.execute("SELECT date, channel, product, cost_amt FROM sales ORDER BY id")
    rows = cur.fetchall()
    con.close()
    assert rows == [
        ("2025-01-01", "online", "p", 5.0),
        ("2025-01-02", "retail", "p", 7.0),
    ]

    out_file = tmp_path / "export.xlsx"
    database.export_to_excel(str(out_file))
    df_out = pd.read_excel(out_file, "Sales")
    assert len(df_out) == 2
    assert list(df_out["channel"]) == ["online", "retail"]
