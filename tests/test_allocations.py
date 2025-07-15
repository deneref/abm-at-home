import os
import sys
import sqlite3
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database

def parse_id(value):
    try:
        return int(value.split(":")[0]) if value else None
    except Exception:
        return None

DB = database.DB_NAME

def setup_module(module):
    if os.path.exists(DB):
        os.remove(DB)
    database.init_db()
    database.reset_all_tables()


def test_parse_id():
    assert parse_id("10: Driver") == 10
    assert parse_id("") is None


def test_allocation_cost_split():
    con = database.get_connection()
    cur = con.cursor()
    # create driver and cost objects
    cur.execute("INSERT INTO drivers(name) VALUES('drv')")
    driver_id = cur.lastrowid
    cur.execute("INSERT INTO cost_objects(name) VALUES('o1')")
    co1 = cur.lastrowid
    cur.execute("INSERT INTO cost_objects(name) VALUES('o2')")
    co2 = cur.lastrowid
    cur.execute("INSERT INTO driver_values(driver_id,cost_object_nm,value) VALUES(?,?,?)", (driver_id,'o1',2))
    cur.execute("INSERT INTO driver_values(driver_id,cost_object_nm,value) VALUES(?,?,?)", (driver_id,'o2',1))
    cur.execute("INSERT INTO resources(name,cost_total,unit) VALUES('res',100,'u')")
    res_id = cur.lastrowid
    cur.execute("INSERT INTO activities(name,driver_id,evenly) VALUES('act',?,0)", (driver_id,))
    act_id = cur.lastrowid
    cur.execute("INSERT INTO resource_allocations(resource_id,activity_id,amount) VALUES(?,?,1)", (res_id, act_id))
    con.commit()
    con.close()

    database.apply_driver_values()
    database.update_activity_costs()

    con = database.get_connection()
    cur = con.cursor()
    cur.execute("SELECT allocated_cost FROM activities WHERE id=?", (act_id,))
    act_cost = cur.fetchone()[0]
    cur.execute("SELECT driver_amt, allocated_cost FROM activity_allocations WHERE activity_id=? AND cost_object_id=?", (act_id, co1))
    da1 = cur.fetchone()
    cur.execute("SELECT driver_amt, allocated_cost FROM activity_allocations WHERE activity_id=? AND cost_object_id=?", (act_id, co2))
    da2 = cur.fetchone()
    con.close()

    assert da1[0] == 2
    assert da2[0] == 1
    exp1 = pytest.approx(act_cost * 2 / 3)
    exp2 = pytest.approx(act_cost * 1 / 3)
    assert da1[1] == exp1
    assert da2[1] == exp2


def test_unallocated_cost_calculation():
    # start from a clean state
    database.reset_all_tables()
    con = database.get_connection()
    cur = con.cursor()
    cur.execute("INSERT INTO resources(name,cost_total,unit) VALUES('r1',200,'u')")
    r_id = cur.lastrowid
    cur.execute("INSERT INTO activities(name,driver_id,evenly) VALUES('a1',NULL,0)")
    a1 = cur.lastrowid
    cur.execute("INSERT INTO activities(name,driver_id,evenly) VALUES('a2',NULL,0)")
    a2 = cur.lastrowid
    con.commit()
    con.close()

    rows = database.get_resources_with_unallocated()
    assert rows[0][0] == r_id
    assert rows[0][4] == 200

    con = database.get_connection()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO resource_allocations(resource_id,activity_id,amount) VALUES(?,?,?)",
        (r_id, a1, 50),
    )
    cur.execute(
        "INSERT INTO resource_allocations(resource_id,activity_id,amount) VALUES(?,?,?)",
        (r_id, a2, 20),
    )
    con.commit()
    con.close()

    rows = database.get_resources_with_unallocated()
    assert rows[0][4] == pytest.approx(130)
