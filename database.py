import sqlite3
from contextlib import contextmanager

DB_NAME = "abm_data.db"


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
    """
    )
    con.commit()
    con.close()
