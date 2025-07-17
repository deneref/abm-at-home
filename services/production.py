"""Functions related to produced amount management."""

from __future__ import annotations


def set_produced_amount(product: str, amount: float) -> None:
    """Insert or update produced amount for a given product."""
    from database import get_connection

    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "INSERT INTO produced_amounts(product, amount) VALUES(?, ?) "
        "ON CONFLICT(product) DO UPDATE SET amount=excluded.amount",
        (product, amount),
    )
    con.commit()
    con.close()


def get_produced_amount(product: str) -> float | None:
    """Return produced amount for the product if exists."""
    from database import get_connection

    con = get_connection()
    cur = con.cursor()
    cur.execute(
        "SELECT amount FROM produced_amounts WHERE product=?",
        (product,),
    )
    row = cur.fetchone()
    con.close()
    return row[0] if row else None


def get_all_produced_amounts():
    """Return list of (product, amount) for all produced amounts."""
    from database import get_connection

    con = get_connection()
    cur = con.cursor()
    cur.execute("SELECT product, amount FROM produced_amounts")
    rows = cur.fetchall()
    con.close()
    return rows
