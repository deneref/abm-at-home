import sqlite3
from contextlib import contextmanager
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

    # ── вспомогательная функция ────────────────────────────────────────────────
    def add_column_if_missing(table: str, col_def: str) -> None:
        col_name = col_def.split()[0]
        cur.execute(f"PRAGMA table_info({table})")
        if col_name not in [row[1] for row in cur.fetchall()]:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")

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
        driver TEXT                        -- временно, для миграции
    );

    CREATE TABLE IF NOT EXISTS cost_objects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
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
        quantity REAL NOT NULL,
        PRIMARY KEY (activity_id, cost_object_id),
        FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE,
        FOREIGN KEY (cost_object_id) REFERENCES cost_objects(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS drivers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS driver_values (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        driver_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        value REAL NOT NULL,
        FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE,
        UNIQUE(driver_id, description)
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

    CREATE TABLE IF NOT EXISTS resource_allocations_monthly (
        resource_id INTEGER NOT NULL,
        activity_id INTEGER NOT NULL,
        period TEXT NOT NULL,
        amount REAL NOT NULL,
        PRIMARY KEY(resource_id, activity_id, period),
        FOREIGN KEY(resource_id) REFERENCES resources(id) ON DELETE CASCADE,
        FOREIGN KEY(activity_id) REFERENCES activities(id) ON DELETE CASCADE,
        FOREIGN KEY(period) REFERENCES periods(period) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS activity_allocations_monthly (
        activity_id INTEGER NOT NULL,
        cost_object_id INTEGER NOT NULL,
        period TEXT NOT NULL,
        quantity REAL NOT NULL,
        driver_value_id INTEGER,
        PRIMARY KEY(activity_id, cost_object_id, period),
        FOREIGN KEY(activity_id) REFERENCES activities(id) ON DELETE CASCADE,
        FOREIGN KEY(cost_object_id) REFERENCES cost_objects(id) ON DELETE CASCADE,
        FOREIGN KEY(driver_value_id) REFERENCES driver_values(id) ON DELETE RESTRICT,
        FOREIGN KEY(period) REFERENCES periods(period) ON DELETE CASCADE
    );
    """
    )
    con.commit()

    # ── новые столбцы в activities ────────────────────────────────────────────
    add_column_if_missing(
        "activities",
        "driver_id INTEGER REFERENCES drivers(id) ON DELETE RESTRICT",
    )
    add_column_if_missing(
        "activities",
        "evenly INTEGER NOT NULL DEFAULT 0",
    )

    # ── миграция старого текстового driver ────────────────────────────────────
    cur.execute("PRAGMA table_info(activities)")
    columns = [col[1] for col in cur.fetchall()]
    if "driver" in columns:
        cur.execute(
            """
            INSERT OR IGNORE INTO drivers(name)
                SELECT DISTINCT driver FROM activities
                WHERE driver IS NOT NULL
            """
        )
        cur.execute(
            """
            UPDATE activities
               SET driver_id = (
                    SELECT id FROM drivers
                     WHERE name = activities.driver
               )
             WHERE driver IS NOT NULL
            """
        )
        try:
            cur.execute("ALTER TABLE activities DROP COLUMN driver")
        except sqlite3.OperationalError:
            # если SQLite старее 3.35, DROP COLUMN недоступен
            pass

    # ── заполнение помесячных таблиц (идемпотентно) ──────────────────────────
    cur.executescript(
        """
    INSERT OR IGNORE INTO resource_costs(resource_id, period, cost)
        SELECT r.id, p.period, r.cost_total
          FROM resources r
               CROSS JOIN periods p;

    INSERT OR IGNORE INTO resource_allocations_monthly(resource_id, activity_id, period, amount)
        SELECT ra.resource_id, ra.activity_id, p.period, ra.amount
          FROM resource_allocations ra
               CROSS JOIN periods p;

    INSERT OR IGNORE INTO activity_allocations_monthly(activity_id, cost_object_id, period, quantity)
        SELECT aa.activity_id, aa.cost_object_id, p.period, aa.quantity
          FROM activity_allocations aa
               CROSS JOIN periods p;
    """
    )

    con.commit()
    con.close()


def insert_data():
    con = get_connection()
    cur = con.cursor()

    # ── заполнение помесячных таблиц (идемпотентно) ──────────────────────────
    cur.executescript(
        """
    delete from cost_objects;
    INSERT OR IGNORE INTO cost_objects(name)
        VALUES 
        ("Кепка цветок-солнце Графит")
        ,("Кепка цветок-солнце Маджента")
        ,("Кепка цветок-солнце Бежевая")
        ,("Кепка День Графит")
        ,("Кепка День Маджента")
        ,("Лонгслив Мартини")
        ,("Лонгслив Камминг Белый")
        ,("Лонгслив Камминг Розовый")
        ,("Лонгслив Тайгер Белый")
        ,("Лонгслив Тайгер Розовый")
        ,("Худи Оливки")
        ,("Худи Камминг Графит")
        ,("Худи Камминг Синий")
        ,("Худи Лаверс Графит")
        ,("Худи Лаверс Синий")
        ;

        delete from drivers;
        insert into drivers(name)
        values("Отзывы Я.Маркет (кол-во)")
        ,("Продано Я.Маркет (шт)")
        ,("Постов instagram")
        ;

         -- данные на 11.07.2025
         delete from resources;
         INSERT OR IGNORE INTO resources(name, cost_total, unit)
         values
         ("Размещение на витрине Яндекс", 195830, "рубли")
         ,("Продвижение Яндекс", 100.0, "рубли")
         ,("Отзывы Яндекс Маркет", 15152, "рубли")
         ,("Буст Яндекс Маркет", 29706, "рубли")
         ,("Полки Яндекс Маркет ", 6403, "рубли")
         ,("Доставка Яндекс Маркет ", 75420, "рубли")
         ,("Перевод платежа Яндекс Маркет ", 19362, "рубли")
         ,("Поставка (транзитный склад)", 5700, "рубли")
         ,("Яся ФОТ", 70000, "рубли")
         ,("Налог", 70000, "рубли")
         ,("Стоимость кредита", 70000, "рубли")
         ,("Займ родители Дани", 20000, "рубли")
         ,("Займ родители Антона", 28000, "рубли")
         ;

         delete from activities;
         INSERT OR IGNORE INTO activities(name, driver_id)
         values("Получение отзывов X Яндекс Маркет", 1)
         ,("Функционирование X Яндекс Маркет", 1)
         ,("Функционирование X Оплата кредита", 1)
         ,("Функционирование X Оплата займов", 1)
         ,("Разработка X Дизайн", 1)
         ,("Разработка X Пошив Пробников", 1)
         ,("Производство X Упаковка", 1)
         ,("Производство X Пошив", 1)
         ,("Производство X Пошив", 1)
        ;
    """
    )

    con.commit()
    con.close()


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
    cur.execute("SELECT id, name FROM cost_objects")
    cos = cur.fetchall()
    df_costobj = pd.DataFrame(cos, columns=["id", "name"])
    # Drivers
    cur.execute("SELECT id, name FROM drivers")
    dr = cur.fetchall()
    df_drivers = pd.DataFrame(dr, columns=["id", "name"])
    # Driver Values (with driver name)
    cur.execute("""SELECT dv.id, d.name AS driver, dv.description, dv.value
                   FROM driver_values dv
                   JOIN drivers d ON dv.driver_id = d.id""")
    dvs = cur.fetchall()
    df_driver_vals = pd.DataFrame(
        dvs, columns=["id", "driver", "description", "value"])
    # Resource Allocations (with resource and activity names)
    cur.execute("""SELECT r.id, r.name, a.id, a.name, ra.amount
                   FROM resource_allocations ra
                   JOIN resources r ON ra.resource_id = r.id
                   JOIN activities a ON ra.activity_id = a.id""")
    ra = cur.fetchall()
    df_res_alloc = pd.DataFrame(ra, columns=[
                                "resource_id", "resource_name", "activity_id", "activity_name", "amount"])
    # Activity Allocations (with activity and cost_object names, and driver value description)
    cur.execute("""SELECT a.id, a.name, c.id, c.name,
                          IFNULL(dv.description, '') AS driver_value,
                          aa.quantity
                   FROM activity_allocations aa
                   JOIN activities a ON aa.activity_id = a.id
                   JOIN cost_objects c ON aa.cost_object_id = c.id
                   LEFT JOIN driver_values dv ON aa.driver_value_id = dv.id""")
    aa = cur.fetchall()
    df_act_alloc = pd.DataFrame(aa, columns=[
                                "activity_id", "activity_name", "cost_object_id", "cost_object_name", "driver_value", "quantity"])
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
        "resource_allocations_monthly", "activity_allocations_monthly", "resource_costs",
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
        desc = str(row["description"]).strip()
        if not driver_name or not desc:
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
                "INSERT OR IGNORE INTO driver_values(id, driver_id, description, value) VALUES(?, ?, ?, ?)",
                (dv_id, d_id, desc, value)
            )
            cur.execute(
                "UPDATE driver_values SET driver_id=?, description=?, value=? WHERE id=?",
                (d_id, desc, value, dv_id)
            )
        else:
            cur.execute("INSERT INTO driver_values(driver_id, description, value) VALUES(?, ?, ?)",
                        (d_id, desc, value))
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
        qty = float(row["quantity"]) if pd.notna(row["quantity"]) else None

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
            # If a driver value description is provided, find its ID (unique within driver)
            # First, get the activity's driver_id to narrow search
            cur.execute(
                "SELECT driver_id, evenly FROM activities WHERE id=?", (a_id,))
            act_info = cur.fetchone()
            act_driver_id = act_info[0] if act_info else None
            act_evenly = act_info[1] if act_info else 0
            if act_driver_id:
                cur.execute("SELECT id FROM driver_values WHERE driver_id=? AND description=?",
                            (act_driver_id, drv_desc))
                val = cur.fetchone()
                if val:
                    driver_value_id = val[0]
            if driver_value_id is None:
                # Try find by description globally if unique
                cur.execute(
                    "SELECT id FROM driver_values WHERE description=?", (drv_desc,))
                vals = cur.fetchall()
                if len(vals) == 1:
                    driver_value_id = vals[0][0]
        # Determine quantity to store
        qty_val = 0.0
        cur.execute(
            "SELECT driver_id, evenly FROM activities WHERE id=?", (a_id,))
        a_info = cur.fetchone()
        act_driver = a_info[0] if a_info else None
        act_evenly = a_info[1] if a_info else 0
        if act_evenly == 1:
            qty_val = 1.0
            driver_value_id = None  # evenly distribution doesn't use driver values
        elif act_driver and driver_value_id:
            # lookup the actual numeric value for the driver value
            cur.execute("SELECT value FROM driver_values WHERE id=?",
                        (driver_value_id,))
            val = cur.fetchone()
            qty_val = float(val[0]) if val else 0.0
        else:
            # manual quantity
            qty_val = float(qty) if qty is not None else 0.0

        cur.execute(
            "INSERT OR IGNORE INTO activity_allocations(activity_id, cost_object_id, quantity, driver_value_id) VALUES(?, ?, ?, ?)",
            (a_id, c_id, qty_val, driver_value_id)
        )
        cur.execute(
            "UPDATE activity_allocations SET quantity=?, driver_value_id=? WHERE activity_id=? AND cost_object_id=?",
            (qty_val, driver_value_id, a_id, c_id)
        )

    # Regenerate period-specific tables (resource_costs and monthly allocations)
    cur.executescript("""
        DELETE FROM resource_costs;
        INSERT OR IGNORE INTO resource_costs(resource_id, period, cost)
            SELECT r.id, p.period, r.cost_total
            FROM resources r CROSS JOIN periods p;
        DELETE FROM resource_allocations_monthly;
        INSERT OR IGNORE INTO resource_allocations_monthly(resource_id, activity_id, period, amount)
            SELECT ra.resource_id, ra.activity_id, p.period, ra.amount
            FROM resource_allocations ra CROSS JOIN periods p;
        DELETE FROM activity_allocations_monthly;
        INSERT OR IGNORE INTO activity_allocations_monthly(activity_id, cost_object_id, period, quantity, driver_value_id)
            SELECT aa.activity_id, aa.cost_object_id, p.period, aa.quantity, aa.driver_value_id
            FROM activity_allocations aa CROSS JOIN periods p;
    """)
    con.commit()
    con.close()
