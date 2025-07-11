import sqlite3
from contextlib import contextmanager

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
    """
    )

    con.commit()
    con.close()
