import sqlite3
from contextlib import contextmanager

DB_NAME = "abm_data.db"
current_period = None  # Currently selected period (YYYY-MM)


def get_connection():
    con = sqlite3.connect(DB_NAME)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    con = get_connection()
    cur = con.cursor()
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
        driver TEXT NOT NULL
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

    /* New tables for drivers and monthly details */
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

    /* Extend activities table for driver references and even distribution flag */
    ALTER TABLE activities
        ADD COLUMN driver_id INTEGER REFERENCES drivers(id) ON DELETE RESTRICT;
    ALTER TABLE activities
        ADD COLUMN evenly INTEGER NOT NULL DEFAULT 0;

    /* Migrate existing driver data to new structure */
    INSERT OR IGNORE INTO drivers(name)
        SELECT DISTINCT driver FROM activities;
    UPDATE activities
        SET driver_id = (SELECT drivers.id FROM drivers WHERE drivers.name = activities.driver);

    /* Periods table for months Jan 2025 - Jan 2026 */
    CREATE TABLE IF NOT EXISTS periods (
        period TEXT PRIMARY KEY
    );
    INSERT OR IGNORE INTO periods(period) VALUES
        ('2025-01'),('2025-02'),('2025-03'),('2025-04'),('2025-05'),('2025-06'),
        ('2025-07'),('2025-08'),('2025-09'),('2025-10'),('2025-11'),('2025-12'),('2026-01');

    /* Monthly values tables */
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

    /* Populate monthly tables with existing data */
    INSERT OR IGNORE INTO resource_costs(resource_id, period, cost)
        SELECT r.id, p.period, r.cost_total
        FROM resources r, periods p;
    INSERT OR IGNORE INTO resource_allocations_monthly(resource_id, activity_id, period, amount)
        SELECT ra.resource_id, ra.activity_id, p.period, ra.amount
        FROM resource_allocations ra, periods p;
    INSERT OR IGNORE INTO activity_allocations_monthly(activity_id, cost_object_id, period, quantity, driver_value_id)
        SELECT aa.activity_id, aa.cost_object_id, p.period, aa.quantity, aa.driver_value_id
        FROM activity_allocations aa, periods p;

    /* Remove old driver text column */
    ALTER TABLE activities DROP COLUMN driver;
    """
    )
    con.commit()
    con.close()
