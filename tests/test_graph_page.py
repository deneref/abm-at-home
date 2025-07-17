import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database
from graph_logic import build_graph_data

DB = database.DB_NAME

def setup_module(module):
    if os.path.exists(DB):
        os.remove(DB)
    database.init_db()
    database.reset_all_tables()
    database.current_period = '2025-01'

    con = database.get_connection()
    cur = con.cursor()
    # resources
    cur.execute("INSERT INTO resources(name,cost_total,unit) VALUES('R1',100,'u')")
    res = cur.lastrowid
    # activities
    cur.execute("INSERT INTO activities(business_procces,activity,driver_id,evenly) VALUES('bp1','a1',NULL,0)")
    act1 = cur.lastrowid
    cur.execute("INSERT INTO activities(business_procces,activity,driver_id,evenly) VALUES('bp2','a2',NULL,0)")
    act2 = cur.lastrowid
    # cost objects
    cur.execute("INSERT INTO cost_objects(product,business_procces) VALUES('p1','b1')")
    co1 = cur.lastrowid
    cur.execute("INSERT INTO cost_objects(product,business_procces) VALUES('p1','b2')")
    co2 = cur.lastrowid
    cur.execute("INSERT INTO cost_objects(product,business_procces) VALUES('p2','b1')")
    co3 = cur.lastrowid
    # allocations
    cur.execute("INSERT INTO resource_allocations(resource_id,activity_id,amount) VALUES(?,?,1)", (res, act1))
    cur.execute("INSERT INTO resource_allocations(resource_id,activity_id,amount) VALUES(?,?,1)", (res, act2))
    cur.execute("INSERT INTO activity_allocations(activity_id,cost_object_id,driver_amt) VALUES(?,?,1)", (act1, co1))
    cur.execute("INSERT INTO activity_allocations(activity_id,cost_object_id,driver_amt) VALUES(?,?,1)", (act1, co2))
    cur.execute("INSERT INTO activity_allocations(activity_id,cost_object_id,driver_amt) VALUES(?,?,1)", (act2, co3))
    con.commit()
    con.close()
    database.update_activity_costs()


def test_product_filter():
    labels, _, edges = build_graph_data('p1')
    nodes = set(labels.keys())
    assert any(n.startswith('O') and 'p1' in labels[n] for n in nodes)
    assert all(not labels[n].startswith('O: p2') for n in nodes)
    edge_targets = {e[1] for e in edges if e[1].startswith('O')}
    assert edge_targets == {'O1', 'O2'}


def test_product_and_bproc_filter():
    labels, _, edges = build_graph_data('p1', 'b2')
    nodes = set(labels.keys())
    # only cost object with b2
    assert any('b2' in labels[n] for n in nodes if n.startswith('O'))
    assert all('b2' in labels[n] for n in nodes if n.startswith('O'))
    edge_targets = {e[1] for e in edges if e[1].startswith('O')}
    assert edge_targets == {'O2'}
    # only activity a1 connected
    assert any(e[0] == 'A1' for e in edges)
    assert all(e[0] != 'A2' for e in edges)
