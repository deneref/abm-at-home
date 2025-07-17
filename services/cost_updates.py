"""Service functions for cost recalculation across activities and cost objects."""

from __future__ import annotations

# Functions import database lazily to avoid circular imports


def update_activity_costs() -> None:
    """Recalculate allocated cost for each activity based on current resource allocations."""
    from database import get_connection

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
           SET allocated_cost = COALESCE(
                (
                    SELECT SUM(
                               CASE WHEN totals.total_amt > 0
                                    THEN r.cost_total * ra.amount / totals.total_amt
                                    ELSE 0 END)
                      FROM resource_allocations ra
                      JOIN resources r ON r.id = ra.resource_id
                      JOIN totals ON totals.resource_id = ra.resource_id
                     WHERE ra.activity_id = activities.id
                ),
                0
           )
        """
    )
    con.commit()
    con.close()
    update_cost_object_costs()


def update_activity_allocation_costs() -> None:
    """Update allocated_cost for each activity allocation based on driver amounts."""
    from database import get_connection

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
    from database import get_connection

    con = get_connection()
    cur = con.cursor()
    cur.execute(
        """
        UPDATE cost_objects
           SET allocated_cost = COALESCE(
                (
                    SELECT SUM(aa.allocated_cost)
                      FROM activity_allocations aa
                     WHERE aa.cost_object_id = cost_objects.id
                ),
                0
           )
        """
    )
    con.commit()
    con.close()
