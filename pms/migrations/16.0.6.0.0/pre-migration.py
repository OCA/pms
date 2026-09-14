# Copyright 2026 Commit [Sun]
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Turn the sale restrictions from one row per night into date ranges.

Everything happens here and not in a post-migration because ``date_from`` and
``date_to`` are required: the columns have to exist and be populated before
the ORM updates the schema, or it cannot set them NOT NULL.

The rows are not rebuilt. Consecutive nights holding the same values collapse
onto the FIRST of them, which keeps its id, its creation date and anything
pointing at it, and the rest are deleted. Nothing is lost in the process: a
run of nights with no restriction at all survives as a range that says so.
"""
import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# The seven values that define a restriction. Two rows of consecutive nights
# belong to the same range when all of them match.
_VALUES = (
    "min_stay",
    "min_stay_arrival",
    "max_stay",
    "max_stay_arrival",
    "closed",
    "closed_arrival",
    "closed_departure",
)

_ADD_COLUMNS = """
    ALTER TABLE pms_availability_plan_rule
        ADD COLUMN IF NOT EXISTS date_from date,
        ADD COLUMN IF NOT EXISTS date_to date
"""

# What the table said night by night, to check the ranges against once they
# are written. A temp table so that it goes away with the session.
_SNAPSHOT = """
    CREATE TEMP TABLE pms_availability_plan_rule_migration_night AS
    SELECT
        availability_plan_id,
        pms_property_id,
        room_type_id,
        date,
        {values}
    FROM pms_availability_plan_rule
    WHERE date IS NOT NULL
"""

# Subtracting the row number from the date gives a constant over a run of
# consecutive dates, so the grouping breaks both when a value changes and when
# a night has no row at all.
_COLLAPSE = """
    WITH numbered AS (
        SELECT
            id,
            availability_plan_id,
            pms_property_id,
            room_type_id,
            date,
            {values},
            date - (
                ROW_NUMBER() OVER (
                    PARTITION BY
                        availability_plan_id,
                        pms_property_id,
                        room_type_id,
                        {values}
                    ORDER BY date
                )
            )::int AS run
        FROM pms_availability_plan_rule
        WHERE date IS NOT NULL
    ), grouped AS (
        SELECT
            (ARRAY_AGG(id ORDER BY date, id))[1] AS keep_id,
            MIN(date) AS date_from,
            MAX(date) AS date_to
        FROM numbered
        GROUP BY
            availability_plan_id,
            pms_property_id,
            room_type_id,
            {values},
            run
    )
    UPDATE pms_availability_plan_rule rule
    SET date_from = grouped.date_from,
        date_to = grouped.date_to
    FROM grouped
    WHERE rule.id = grouped.keep_id
"""

# Every night of every run other than the first. Their bindings go with them
# through the cascade they declare, which is what the connector expects: what
# it identified per night was a locally generated id, not anything the channel
# manager knows about.
_DROP_COLLAPSED = """
    DELETE FROM pms_availability_plan_rule
    WHERE date_from IS NULL AND date IS NOT NULL
"""

# Rows the old model could hold and a range cannot express. They configured
# nothing that could be resolved either, since a rule with no night never
# entered any search by date.
_DROP_WITHOUT_DATE = """
    DELETE FROM pms_availability_plan_rule WHERE date IS NULL RETURNING id
"""

# The ranges expanded back to nights have to say exactly what the table said.
_CHECK = """
    WITH expanded AS (
        SELECT
            rule.availability_plan_id,
            rule.pms_property_id,
            rule.room_type_id,
            night.date::date AS date,
            {values_prefixed}
        FROM pms_availability_plan_rule rule
        CROSS JOIN LATERAL generate_series(
            rule.date_from, rule.date_to, INTERVAL '1 day'
        ) AS night(date)
    )
    SELECT
        COUNT(*) FILTER (WHERE expanded.date IS NULL) AS lost,
        COUNT(*) FILTER (WHERE night.date IS NULL) AS invented
    FROM expanded
    FULL OUTER JOIN pms_availability_plan_rule_migration_night night
        ON night.availability_plan_id = expanded.availability_plan_id
       AND night.pms_property_id = expanded.pms_property_id
       AND night.room_type_id = expanded.room_type_id
       AND night.date = expanded.date
       AND {values_match}
"""


@openupgrade.migrate()
def migrate(env, version):
    if not openupgrade.column_exists(env.cr, "pms_availability_plan_rule", "date"):
        _logger.warning("The availability plan rules are already ranges.")
        return
    values = ", ".join(_VALUES)
    openupgrade.logged_query(env.cr, _ADD_COLUMNS)
    openupgrade.logged_query(env.cr, _SNAPSHOT.format(values=values))
    openupgrade.logged_query(env.cr, _COLLAPSE.format(values=values))
    openupgrade.logged_query(env.cr, _DROP_COLLAPSED)

    env.cr.execute(_DROP_WITHOUT_DATE)
    without_date = env.cr.fetchall()
    if without_date:
        _logger.warning(
            "%s availability plan rule(s) had no date and could not become a "
            "range, they were dropped. First ids: %s",
            len(without_date),
            [row[0] for row in without_date[:20]],
        )

    _check(env, values)

    # The nights are in the ranges now, so the column is only kept as the
    # material to roll back with.
    openupgrade.rename_columns(env.cr, {"pms_availability_plan_rule": [("date", None)]})


def _check(env, values):
    """Abort the upgrade if the ranges do not say what the rows said.

    The migration runs inside the transaction of the update, so raising here
    rolls the whole thing back instead of leaving the restrictions rewritten
    into something else.
    """
    env.cr.execute(
        _CHECK.format(
            values_prefixed=", ".join(f"rule.{value}" for value in _VALUES),
            values_match=" AND ".join(
                f"night.{value} = expanded.{value}" for value in _VALUES
            ),
        )
    )
    lost, invented = env.cr.fetchone()
    _logger.info(
        "Sale restrictions collapsed into ranges: %s night(s) lost, %s invented.",
        lost,
        invented,
    )
    if lost or invented:
        raise ValueError(
            "The collapse of the sale restrictions into ranges is not "
            f"equivalent to the rows it replaces: {lost} night(s) lost, "
            f"{invented} invented."
        )
