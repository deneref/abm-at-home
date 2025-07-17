import os
import sys
import sqlite3
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import database

DB = database.DB_NAME

def setup_module(module):
    if os.path.exists(DB):
        os.remove(DB)
    database.init_db()
    database.reset_all_tables()


def test_set_and_get_produced_amount():
    database.set_produced_amount('prod1', 50)
    amt = database.get_produced_amount('prod1')
    assert amt == 50


def test_unit_cost_computation():
    con = database.get_connection()
    cur = con.cursor()
    cur.execute("INSERT INTO cost_objects(product,business_procces,allocated_cost) VALUES('prod2','bp',120)")
    con.commit()
    con.close()
    database.set_produced_amount('prod2', 10)
    con = database.get_connection()
    cur = con.cursor()
    cur.execute("""SELECT c.allocated_cost, pa.amount FROM cost_objects c
                   LEFT JOIN produced_amounts pa ON pa.product=c.product
                   WHERE c.product='prod2'""")
    alloc, amt = cur.fetchone()
    con.close()
    assert alloc == 120
    assert amt == 10
    assert pytest.approx(alloc / amt) == 12
