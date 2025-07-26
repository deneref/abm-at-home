import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database

DB = database.DB_NAME


def setup_module(module):
    if os.path.exists(DB):
        os.remove(DB)
    database.init_db()
    database.reset_all_tables()
    database.current_period = '2025-01'

    con = database.get_connection()
    cur = con.cursor()
    # resource and activity
    cur.execute("INSERT INTO resources(name,cost_total,unit) VALUES('Res', 100, 'u')")
    res = cur.lastrowid
    cur.execute("INSERT INTO activities(business_procces,activity,driver_id,evenly) VALUES('bp','act',NULL,0)")
    act = cur.lastrowid
    # cost object
    cur.execute("INSERT INTO cost_objects(product,business_procces) VALUES('p1','bp')")
    co = cur.lastrowid
    # allocations
    cur.execute("INSERT INTO resource_allocations(resource_id,activity_id,amount) VALUES(?,?,1)", (res, act))
    cur.execute("INSERT INTO activity_allocations(activity_id,cost_object_id,driver_amt) VALUES(?,?,1)", (act, co))
    # sales
    cur.execute("INSERT INTO sales(date, channel, product, cost_amt) VALUES('2025-01-01','online','p1',50)")
    cur.execute("INSERT INTO sales(date, channel, product, cost_amt) VALUES('2025-01-02','retail','p1',70)")
    con.commit()
    con.close()
    database.update_activity_costs()


def test_revenue_and_cost_aggregation():
    revenue, cost = database.get_revenue_and_cost('p1')
    assert revenue == 120
    # cost_objects should hold the allocated cost
    con = database.get_connection()
    cur = con.cursor()
    cur.execute("SELECT allocated_cost FROM cost_objects WHERE product='p1'")
    alloc = cur.fetchone()[0]
    con.close()
    assert cost == alloc
