import sqlite3
import pandas as pd

DB_NAME = "abm_data.db"
current_period = None  # Currently selected period (YYYY-MM)


def get_connection():
    con = sqlite3.connect(DB_NAME)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    import sqlite3
    con = get_connection()
    cur = con.cursor()

    # ── базовые таблицы ────────────────────────────────────────────────────────
    cur.executescript(
        """

    CREATE TABLE IF NOT EXISTS resources (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        cost_total REAL NOT NULL,
        unit TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        driver_id INTEGER REFERENCES drivers(id) ON DELETE RESTRICT,
        evenly INTEGER NOT NULL DEFAULT 0,
        allocated_cost REAL NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS cost_objects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        allocated_cost REAL NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS resource_allocations (
        resource_id INTEGER NOT NULL,
        activity_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        PRIMARY KEY (resource_id, activity_id),
        FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE,
        FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS activity_allocations (
        activity_id INTEGER NOT NULL,
        cost_object_id INTEGER NOT NULL,
        driver_amt INTEGER NOT NULL,
        driver_value_id INTEGER,
        allocated_cost REAL NOT NULL DEFAULT 0,
        PRIMARY KEY (activity_id, cost_object_id),
        FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
        FOREIGN KEY (cost_object_id) REFERENCES cost_objects(id) ON DELETE CASCADE,
        FOREIGN KEY (driver_value_id) REFERENCES driver_values(id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS driver_values (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_id INTEGER NOT NULL,
        cost_object_nm TEXT NOT NULL,
        value REAL NOT NULL,
        FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE,
        UNIQUE(driver_id, cost_object_nm)
    );

    CREATE TABLE IF NOT EXISTS periods (
        period TEXT PRIMARY KEY
    );

    INSERT OR IGNORE INTO periods(period) VALUES
        ('2025-01'),('2025-02'),('2025-03'),('2025-04'),('2025-05'),('2025-06'),
        ('2025-07'),('2025-08'),('2025-09'),('2025-10'),('2025-11'),('2025-12'),
        ('2026-01');

    CREATE TABLE IF NOT EXISTS resource_costs (
        resource_id INTEGER NOT NULL,
        period TEXT NOT NULL,
        cost REAL NOT NULL,
        PRIMARY KEY(resource_id, period),
        FOREIGN KEY(resource_id) REFERENCES resources(id) ON DELETE CASCADE,
        FOREIGN KEY(period) REFERENCES periods(period) ON DELETE CASCADE
    );

    """
    )
    con.commit()

    # ── заполнение периодических таблиц (идемпотентно) ───────────────────────
    cur.executescript(
        """
    INSERT OR IGNORE INTO resource_costs(resource_id, period, cost)
        SELECT r.id, p.period, r.cost_total
          FROM resources r
               CROSS JOIN periods p;
    """
    )

    con.commit()
    con.close()
    apply_driver_values()
    update_activity_costs()


def update_activity_costs() -> None:
    """Recalculate allocated cost for each activity based on current resource allocations."""
    con = get_connection()
    cur = con.cursor()
    cur.execute(
        """
        WITH totals AS (
            SELECT resource_id, SUM(amount) AS total_amt
              FROM resource_allocations
             GROUP BY resource_id
        )
        UPDATE activities
           SET allocated_cost = COALESCE((
                SELECT SUM(
                           CASE WHEN totals.total_amt > 0
                                THEN r.cost_total * ra.amount / totals.total_amt
                                ELSE 0 END)
                  FROM resource_allocations ra
                  JOIN resources r ON r.id = ra.resource_id
                  JOIN totals ON totals.resource_id = ra.resource_id
                 WHERE ra.activity_id = activities.id
           ), 0)
        """
    )
    con.commit()
    con.close()
    update_cost_object_costs()


def update_activity_allocation_costs() -> None:
    """Update allocated_cost for each activity allocation based on driver amounts."""
    con = get_connection()
    cur = con.cursor()
    cur.execute(
        """
        WITH totals AS (
            SELECT activity_id, SUM(driver_amt) AS total_amt
              FROM activity_allocations
             GROUP BY activity_id
        )
        UPDATE activity_allocations AS aa
           SET allocated_cost = (
                SELECT CASE WHEN totals.total_amt > 0
                            THEN a.allocated_cost * aa.driver_amt / totals.total_amt
                            ELSE 0 END
                  FROM activities a
                  JOIN totals ON totals.activity_id = aa.activity_id
                 WHERE a.id = aa.activity_id
           )
        """
    )
    con.commit()
    con.close()


def update_cost_object_costs() -> None:
    """Recalculate allocated cost for each cost object based on activity allocations."""
    update_activity_allocation_costs()
    con = get_connection()
    cur = con.cursor()
    cur.execute(
        """
        UPDATE cost_objects
           SET allocated_cost = COALESCE((
                SELECT SUM(aa.allocated_cost)
                  FROM activity_allocations aa
                 WHERE aa.cost_object_id = cost_objects.id
           ), 0)
        """
    )
    con.commit()
    con.close()


def update_even_allocations(activity_id: int, evenly: int) -> None:
    """Create or remove cost object allocations for an activity based on
    its evenly flag."""
    con = get_connection()
    cur = con.cursor()
    # Remove existing allocations
    cur.execute(
        "DELETE FROM activity_allocations WHERE activity_id=?",
        (activity_id,),
    )
    if evenly:
        # Even distribution -> allocate driver_amt=1 to each cost object
        cur.execute("SELECT id FROM cost_objects")
        cost_objects = [row[0] for row in cur.fetchall()]
        for co_id in cost_objects:
            cur.execute(
                "INSERT INTO activity_allocations(activity_id, cost_object_id, driver_amt, driver_value_id, allocated_cost) VALUES (?, ?, 1, NULL, 0)",
                (activity_id, co_id),
            )
    con.commit()
    con.close()


def apply_driver_values(dv_ids: list[int] | None = None) -> None:
    """Create or update activity allocations based on driver values.

    If ``dv_ids`` is ``None`` all driver values are processed.
    """
    con = get_connection()
    cur = con.cursor()

    if dv_ids:
        placeholders = ",".join("?" for _ in dv_ids)
        cur.execute(
            f"SELECT id, driver_id, cost_object_nm, value FROM driver_values WHERE id IN ({placeholders})",
            dv_ids,
        )
    else:
        cur.execute(
            "SELECT id, driver_id, cost_object_nm, value FROM driver_values")

    for dv_id, driver_id, co_name, val in cur.fetchall():
        cur.execute("SELECT id FROM cost_objects WHERE name=?", (co_name,))
        row = cur.fetchone()
        if row:
            co_id = row[0]
        else:
            cur.execute("INSERT INTO cost_objects(name) VALUES(?)", (co_name,))
            co_id = cur.lastrowid

        cur.execute("SELECT id FROM activities WHERE driver_id=?", (driver_id,))
        act_ids = [r[0] for r in cur.fetchall()]
        for a_id in act_ids:
            cur.execute(
                "INSERT OR IGNORE INTO activity_allocations(activity_id, cost_object_id, driver_amt, driver_value_id, allocated_cost)"
                " VALUES(?,?,?,?,0)",
                (a_id, co_id, val, dv_id),
            )
            cur.execute(
                "UPDATE activity_allocations SET driver_amt=?, driver_value_id=? WHERE activity_id=? AND cost_object_id=?",
                (val, dv_id, a_id, co_id),
            )

    con.commit()
    con.close()
    update_cost_object_costs()


def insert_data():
    """Load sample data from model.xlsx into the database."""
    import os
    sample_file = os.path.join(os.path.dirname(__file__), "model_new.xlsx")
    if os.path.exists(sample_file):
        try:
            import_from_excel(sample_file)
        except Exception as exc:  # pragma: no cover - show error if sample invalid
            print(f"Failed to import {sample_file}: {exc}")
    else:
        print(f"Model file {sample_file} not found")


def reset_all_tables() -> None:
    """
    Удаляет все данные из всех пользовательских таблиц и сбрасывает
    счётчики AUTOINCREMENT (sqlite_sequence) до 0.
    """
    con = get_connection()
    cur = con.cursor()

    # временно отключаем внешние ключи, чтобы порядок удаления не был важен
    cur.execute("PRAGMA foreign_keys = OFF;")

    # получаем список всех пользовательских таблиц (служебные sqlite_% исключаем)
    cur.execute("""
        SELECT name
          FROM sqlite_master
         WHERE type='table'
           AND name NOT LIKE 'sqlite_%'
    """)
    for (table_name,) in cur.fetchall():
        cur.execute(f'DELETE FROM "{table_name}";')

    # сбрасываем автоинкременты
    cur.execute("DELETE FROM sqlite_sequence;")

    cur.execute("PRAGMA foreign_keys = ON;")
    con.commit()
    con.close()


def export_to_excel(file_path: str):
    """
    Export all model data to an Excel file with multiple sheets.
    Sheets: Resources, Activities, CostObjects, Drivers, DriverValues, ResourceAllocations, ActivityAllocations.
    """
    con = get_connection()
    cur = con.cursor()
    # Fetch data from each table, including names for foreign keys
    # Resources
    cur.execute("SELECT id, name, cost_total, unit FROM resources")
    res = cur.fetchall()
    df_resources = pd.DataFrame(
        res, columns=["id", "name", "cost_total", "unit"])
    # Activities (with driver name instead of id for clarity)
    cur.execute("""SELECT a.id, a.name,
                          IFNULL(d.name, '') AS driver, 
                          a.evenly
                   FROM activities a
                   LEFT JOIN drivers d ON a.driver_id = d.id""")
    acts = cur.fetchall()
    df_activities = pd.DataFrame(
        acts, columns=["id", "name", "driver", "evenly"])
    # Cost Objects
    cur.execute("SELECT id, name, allocated_cost FROM cost_objects")
    cos = cur.fetchall()
    df_costobj = pd.DataFrame(cos, columns=["id", "name", "allocated_cost"])
    # Drivers
    cur.execute("SELECT id, name FROM drivers")
    dr = cur.fetchall()
    df_drivers = pd.DataFrame(dr, columns=["id", "name"])
    # Driver Values (with driver name)
    cur.execute("""SELECT dv.id, d.name AS driver, dv.cost_object_nm, dv.value
                   FROM driver_values dv
                   JOIN drivers d ON dv.driver_id = d.id""")
    dvs = cur.fetchall()
    df_driver_vals = pd.DataFrame(
        dvs, columns=["id", "driver", "cost_object_nm", "value"])
    # Resource Allocations (with resource and activity names)
    cur.execute("""SELECT r.id, r.name, a.id, a.name, ra.amount
                   FROM resource_allocations ra
                   JOIN resources r ON ra.resource_id = r.id
                   JOIN activities a ON ra.activity_id = a.id""")
    ra = cur.fetchall()
    df_res_alloc = pd.DataFrame(ra, columns=[
                                "resource_id", "resource_name", "activity_id", "activity_name", "amount"])
    # Activity Allocations (with activity and cost_object names, and driver value name)
    cur.execute("""SELECT a.id, a.name, c.id, c.name,
                          IFNULL(dv.cost_object_nm, '') AS driver_value,
                          aa.driver_amt, aa.allocated_cost
                   FROM activity_allocations aa
                   JOIN activities a ON aa.activity_id = a.id
                   JOIN cost_objects c ON aa.cost_object_id = c.id
                   LEFT JOIN driver_values dv ON aa.driver_value_id = dv.id""")
    aa = cur.fetchall()
    df_act_alloc = pd.DataFrame(aa, columns=[
                                "activity_id", "activity_name", "cost_object_id", "cost_object_name", "driver_value", "driver_amt", "allocated_cost"])
    con.close()
    # Write dataframes to an Excel file
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        df_resources.to_excel(writer, sheet_name="Resources", index=False)
        df_activities.to_excel(writer, sheet_name="Activities", index=False)
        df_costobj.to_excel(writer, sheet_name="CostObjects", index=False)
        df_drivers.to_excel(writer, sheet_name="Drivers", index=False)
        df_driver_vals.to_excel(writer, sheet_name="DriverValues", index=False)
        df_res_alloc.to_excel(
            writer, sheet_name="ResourceAllocations", index=False)
        df_act_alloc.to_excel(
            writer, sheet_name="ActivityAllocations", index=False)


def import_from_excel(file_path: str):
    """
    Import model data from an Excel file.
    Expects sheets: Resources, Activities, CostObjects, Drivers, DriverValues, ResourceAllocations, ActivityAllocations.
    Clears current data and populates tables from file. Performs upsert by IDs when possible.
    """
    xls = pd.ExcelFile(file_path)
    required_sheets = ["Resources", "Activities", "CostObjects", "Drivers",
                       "DriverValues", "ResourceAllocations", "ActivityAllocations"]
    for sheet in required_sheets:
        if sheet not in xls.sheet_names:
            raise ValueError(f"Missing sheet: {sheet} in Excel file")
    # Read all sheets into DataFrames
    df_resources = pd.read_excel(xls, "Resources")
    df_activities = pd.read_excel(xls, "Activities")
    df_costobj = pd.read_excel(xls, "CostObjects")
    df_drivers = pd.read_excel(xls, "Drivers")
    df_driver_vals = pd.read_excel(xls, "DriverValues")
    df_res_alloc = pd.read_excel(xls, "ResourceAllocations")
    df_act_alloc = pd.read_excel(xls, "ActivityAllocations")

    con = get_connection()
    cur = con.cursor()
    # Clear existing data (like reset_all_tables)
    cur.execute("PRAGMA foreign_keys = OFF;")
    tables = [
        "resource_costs",
        "resource_allocations", "activity_allocations",
        "resources", "activities", "cost_objects",
        "drivers", "driver_values"
    ]
    for t in tables:
        cur.execute(f'DELETE FROM "{t}";')
    cur.execute("DELETE FROM sqlite_sequence;")
    cur.execute("PRAGMA foreign_keys = ON;")

    # Import Drivers
    driver_map = {}  # map driver name to id
    for _, row in df_drivers.iterrows():
        name = str(row["name"]).strip()
        if not name:
            continue
        if pd.notna(row.get("id")):
            d_id = int(row["id"])
            cur.execute(
                "INSERT OR IGNORE INTO drivers(id, name) VALUES(?, ?)",
                (d_id, name)
            )
            cur.execute(
                "UPDATE drivers SET name=? WHERE id=?",
                (name, d_id)
            )
        else:
            # Insert without specified ID
            cur.execute("INSERT INTO drivers(name) VALUES(?)", (name,))
            d_id = cur.lastrowid
        driver_map[name] = d_id

    # Import Resources
    for _, row in df_resources.iterrows():
        name = str(row["name"]).strip()
        if not name:
            continue
        cost_total = float(row["cost_total"]) if pd.notna(
            row["cost_total"]) else 0.0
        unit = str(row["unit"]) if pd.notna(row["unit"]) else ""
        if pd.notna(row.get("id")):
            r_id = int(row["id"])
            cur.execute(
                "INSERT OR IGNORE INTO resources(id, name, cost_total, unit) VALUES(?, ?, ?, ?)",
                (r_id, name, cost_total, unit)
            )
            cur.execute(
                "UPDATE resources SET name=?, cost_total=?, unit=? WHERE id=?",
                (name, cost_total, unit, r_id)
            )
        else:
            cur.execute("INSERT INTO resources(name, cost_total, unit) VALUES(?, ?, ?)",
                        (name, cost_total, unit))

    # Import Activities
    activity_map = {}  # map activity name to id
    for _, row in df_activities.iterrows():
        name = str(row["name"]).strip()
        if not name:
            continue
        # Determine driver_id from driver name, and evenly flag
        driver_name = str(row.get("driver", "")).strip()
        evenly_flag = int(row["evenly"]) if pd.notna(row["evenly"]) else 0
        driver_id = None
        if driver_name:
            driver_id = driver_map.get(driver_name)
            if driver_id is None:
                # If driver not in driver sheet, create a new driver
                cur.execute("INSERT INTO drivers(name) VALUES(?)",
                            (driver_name,))
                driver_id = cur.lastrowid
                driver_map[driver_name] = driver_id
        if pd.notna(row.get("id")):
            a_id = int(row["id"])
            cur.execute(
                "INSERT OR IGNORE INTO activities(id, name, driver_id, evenly) VALUES(?, ?, ?, ?)",
                (a_id, name, driver_id, evenly_flag)
            )
            cur.execute(
                "UPDATE activities SET name=?, driver_id=?, evenly=? WHERE id=?",
                (name, driver_id, evenly_flag, a_id)
            )
        else:
            cur.execute("INSERT INTO activities(name, driver_id, evenly) VALUES(?, ?, ?)",
                        (name, driver_id, evenly_flag))
            a_id = cur.lastrowid
        activity_map[name] = a_id

    # Import Cost Objects
    costobj_map = {}
    for _, row in df_costobj.iterrows():
        name = str(row["name"]).strip()
        if not name:
            continue
        if pd.notna(row.get("id")):
            c_id = int(row["id"])
            cur.execute(
                "INSERT OR IGNORE INTO cost_objects(id, name) VALUES(?, ?)",
                (c_id, name)
            )
            cur.execute(
                "UPDATE cost_objects SET name=? WHERE id=?", (name, c_id))
        else:
            cur.execute("INSERT INTO cost_objects(name) VALUES(?)", (name,))
            c_id = cur.lastrowid
        costobj_map[name] = c_id

    # Import Driver Values
    for _, row in df_driver_vals.iterrows():
        driver_name = str(row["driver"]).strip()
        co_name = str(row["cost_object_nm"]).strip()
        if not driver_name or not co_name:
            continue
        value = float(row["value"]) if pd.notna(row["value"]) else 0.0
        # Ensure driver exists (in case it was not in Drivers sheet but appears here)
        d_id = driver_map.get(driver_name)
        if d_id is None:
            cur.execute("INSERT INTO drivers(name) VALUES(?)", (driver_name,))
            d_id = cur.lastrowid
            driver_map[driver_name] = d_id
        if pd.notna(row.get("id")):
            dv_id = int(row["id"])
            cur.execute(
                "INSERT OR IGNORE INTO driver_values(id, driver_id, cost_object_nm, value) VALUES(?, ?, ?, ?)",
                (dv_id, d_id, co_name, value)
            )
            cur.execute(
                "UPDATE driver_values SET driver_id=?, cost_object_nm=?, value=? WHERE id=?",
                (d_id, co_name, value, dv_id)
            )
        else:
            cur.execute(
                "INSERT INTO driver_values(driver_id, cost_object_nm, value) VALUES(?, ?, ?)",
                (d_id, co_name, value))
            # No need to store dv_id unless we want mapping for something later

    # Import Resource Allocations
    for _, row in df_res_alloc.iterrows():
        # Use provided IDs if available; otherwise lookup by name
        r_id = int(row["resource_id"]) if pd.notna(
            row["resource_id"]) else None
        a_id = int(row["activity_id"]) if pd.notna(
            row["activity_id"]) else None
        r_name = str(row.get("resource_name", "")).strip()
        a_name = str(row.get("activity_name", "")).strip()
        if not r_id and r_name:
            # find resource id by name
            r_id = None
            cur.execute("SELECT id FROM resources WHERE name=?", (r_name,))
            res = cur.fetchone()
            if res:
                r_id = res[0]
        if not a_id and a_name:
            a_id = activity_map.get(a_name)
            if not a_id:
                # find in DB in case not in map
                cur.execute(
                    "SELECT id FROM activities WHERE name=?", (a_name,))
                res = cur.fetchone()
                if res:
                    a_id = res[0]
        if r_id and a_id:
            amount = float(row["amount"]) if pd.notna(row["amount"]) else 0.0
            cur.execute(
                "INSERT OR IGNORE INTO resource_allocations(resource_id, activity_id, amount) VALUES(?, ?, ?)",
                (r_id, a_id, amount)
            )
            cur.execute(
                "UPDATE resource_allocations SET amount=? WHERE resource_id=? AND activity_id=?",
                (amount, r_id, a_id)
            )

    # Import Activity Allocations
    for _, row in df_act_alloc.iterrows():
        a_id = int(row["activity_id"]) if pd.notna(
            row["activity_id"]) else None
        c_id = int(row["cost_object_id"]) if pd.notna(
            row["cost_object_id"]) else None
        a_name = str(row.get("activity_name", "")).strip()
        c_name = str(row.get("cost_object_name", "")).strip()
        drv_desc = str(row.get("driver_value", "")).strip()
        driver_amt = float(row.get("driver_amt", row.get("quantity", 0))) if pd.notna(row.get("driver_amt", row.get("quantity"))) else None

        # Lookup activity and cost object by name if IDs are missing
        if not a_id and a_name:
            a_id = activity_map.get(a_name)
            if not a_id:
                cur.execute(
                    "SELECT id FROM activities WHERE name=?", (a_name,))
                res = cur.fetchone()
                if res:
                    a_id = res[0]
        if not c_id and c_name:
            c_id = costobj_map.get(c_name)
            if not c_id:
                cur.execute(
                    "SELECT id FROM cost_objects WHERE name=?", (c_name,))
                res = cur.fetchone()
                if res:
                    c_id = res[0]
        if not a_id or not c_id:
            continue  # skip invalid references

        # Determine driver_value_id if applicable
        driver_value_id = None
        if drv_desc:
            # If a driver value name is provided, find its ID (unique within driver)
            # First, get the activity's driver_id to narrow search
            cur.execute(
                "SELECT driver_id, evenly FROM activities WHERE id=?", (a_id,))
            act_info = cur.fetchone()
            act_driver_id = act_info[0] if act_info else None
            act_evenly = act_info[1] if act_info else 0
            if act_driver_id:
                cur.execute("SELECT id FROM driver_values WHERE driver_id=? AND cost_object_nm=?",
                            (act_driver_id, drv_desc))
                val = cur.fetchone()
                if val:
                    driver_value_id = val[0]
            if driver_value_id is None:
                # Try find by name globally if unique
                cur.execute(
                    "SELECT id FROM driver_values WHERE cost_object_nm=?", (drv_desc,))
                vals = cur.fetchall()
                if len(vals) == 1:
                    driver_value_id = vals[0][0]
        # Determine driver amount to store
        amt_val = 0.0
        cur.execute(
            "SELECT driver_id, evenly FROM activities WHERE id=?", (a_id,))
        a_info = cur.fetchone()
        act_driver = a_info[0] if a_info else None
        act_evenly = a_info[1] if a_info else 0
        if act_evenly == 1:
            amt_val = 1.0
            driver_value_id = None  # evenly distribution doesn't use driver values
        elif act_driver and driver_value_id:
            # lookup the actual numeric value for the driver value
            cur.execute("SELECT value FROM driver_values WHERE id=?",
                        (driver_value_id,))
            val = cur.fetchone()
            amt_val = float(val[0]) if val else 0.0
        else:
            # manual quantity
            amt_val = float(driver_amt) if driver_amt is not None else 0.0

        cur.execute(
            "INSERT OR IGNORE INTO activity_allocations(activity_id, cost_object_id, driver_amt, driver_value_id, allocated_cost) VALUES(?, ?, ?, ?, 0)",
            (a_id, c_id, amt_val, driver_value_id)
        )
        cur.execute(
            "UPDATE activity_allocations SET driver_amt=?, driver_value_id=? WHERE activity_id=? AND cost_object_id=?",
            (amt_val, driver_value_id, a_id, c_id)
        )

    # Regenerate period-specific tables (resource_costs and monthly allocations)
    cur.executescript(
        """
        DELETE FROM resource_costs;
        INSERT OR IGNORE INTO resource_costs(resource_id, period, cost)
            SELECT r.id, p.period, r.cost_total
            FROM resources r CROSS JOIN periods p;
    """
    )
    con.commit()
    con.close()
    update_activity_costs()
