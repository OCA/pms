# Copyright 2026 Commit [Sun]
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""Move the commercial inventory to ``pms.inventory.rule``.

The inventory lived in one row per (plan, room type, night, property) and is
now a date range with no relation to rates, so the plan dimension collapses:
for each (property, room type, night) the migrated value is the MINIMUM across
the plans that hold a rule, reading ``-1`` as "no limit" so that it never wins
the comparison, and keeping ``0`` as closed.

Only nights from today on. The past is inert for availability and stays in the
legacy columns the pre-migration set aside, which are also the material to
roll back with.
"""
import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

LEGACY_QUOTA = openupgrade.get_legacy_name("quota")
LEGACY_MAX_AVAIL = openupgrade.get_legacy_name("max_avail")
LEGACY_PLAN_AVAIL = openupgrade.get_legacy_name("plan_avail")

# Stands in for the no limit sentinel while comparing, since ``-1`` would
# win every minimum.
INFINITE = 2147483647

# ``plan_avail`` replaced the value with the real availability whenever it was
# negative, so EVERY negative means "no limit" and not just -1 (the past holds
# values down to -12). A NULL reached the record as 0, which is closed.
_NORMALIZE = "GREATEST(COALESCE({column}, 0), -1)"
# ``-1`` is infinity under ``min``, so it is taken out of the aggregation and
# only survives when every plan agrees on it.
_MIN_ACROSS_PLANS = "COALESCE(MIN(NULLIF({value}, -1)), -1)"

# One row per (property, room type, night) with the plan dimension collapsed.
_STAGE_NIGHTS = """
    CREATE TEMP TABLE pms_inventory_migration_night AS
    SELECT
        rule.pms_property_id,
        rule.room_type_id,
        rule.date,
        {min_quota} AS quota,
        {min_max_avail} AS max_avail,
        COUNT(*) AS plans,
        COUNT(DISTINCT {quota}) AS quota_values,
        COUNT(DISTINCT {max_avail}) AS max_avail_values,
        COUNT(*) FILTER (WHERE {quota} <> 0) AS quota_open_plans,
        COUNT(*) FILTER (WHERE {max_avail} <> 0) AS max_avail_open_plans
    FROM pms_availability_plan_rule rule
    WHERE rule.date >= %(cutoff)s
      AND rule.pms_property_id IS NOT NULL
      AND rule.room_type_id IS NOT NULL
    GROUP BY rule.pms_property_id, rule.room_type_id, rule.date
"""

# The room nights every scope has already sold, counted with the predicate the
# resolver uses at runtime: by the room type SOLD and with NO state filter,
# since a cancelled night spent its quota all the same.
_STAGE_CONSUMPTION = """
    CREATE TEMP TABLE pms_inventory_migration_consumption AS
    SELECT
        line.pms_property_id,
        reservation.room_type_id,
        line.date,
        COUNT(*) AS consumed
    FROM pms_reservation_line line
    JOIN pms_reservation reservation ON reservation.id = line.reservation_id
    WHERE line.date >= %(cutoff)s
      AND line.pms_property_id IS NOT NULL
      AND reservation.room_type_id IS NOT NULL
    GROUP BY line.pms_property_id, reservation.room_type_id, line.date
"""

# The stored quota was the REMAINDER: a counter decremented it on every night
# sold. The new model declares the cap and counts the consumption while
# resolving, so the cap has to be rebuilt by adding back what was sold, or
# every night with reservations would be migrated short.
#
# A ``0`` is left alone: it is how a night was closed, and a positive cap
# would reopen it as soon as a reservation is deleted.
_STAGE_CAP = """
    CREATE TEMP TABLE pms_inventory_migration_stage AS
    SELECT
        night.pms_property_id,
        night.room_type_id,
        night.date,
        CASE
            WHEN night.quota > 0
            THEN night.quota + COALESCE(consumption.consumed, 0)
            ELSE night.quota
        END AS quota,
        night.max_avail
    FROM pms_inventory_migration_night night
    LEFT JOIN pms_inventory_migration_consumption consumption
        ON consumption.pms_property_id = night.pms_property_id
       AND consumption.room_type_id = night.room_type_id
       AND consumption.date = night.date
"""

# A rule of the general scope REPLACES the room type defaults in both fields,
# so one that carries exactly the defaults resolves to the same thing as no
# rule at all. Dropping them keeps the table down to what is really
# configured, and the gap it leaves is expressed by the range breaking in two.
_DROP_REDUNDANT = """
    DELETE FROM pms_inventory_migration_stage stage
    USING pms_room_type room_type
    WHERE room_type.id = stage.room_type_id
      AND stage.quota = COALESCE(room_type.default_quota, 0)
      AND stage.max_avail = COALESCE(room_type.default_max_avail, 0)
"""

# Consecutive nights holding the same values become one record. Subtracting
# the row number from the date gives a constant over a run of consecutive
# dates, so the grouping breaks both when a value changes and when a night
# has no row at all.
_COLLAPSE_RANGES = """
    CREATE TEMP TABLE pms_inventory_migration_range AS
    SELECT
        pms_property_id,
        room_type_id,
        quota,
        max_avail,
        MIN(date) AS date_from,
        MAX(date) AS date_to
    FROM (
        SELECT
            stage.*,
            stage.date - (
                ROW_NUMBER() OVER (
                    PARTITION BY
                        stage.pms_property_id,
                        stage.room_type_id,
                        stage.quota,
                        stage.max_avail
                    ORDER BY stage.date
                )
            )::int AS run
        FROM pms_inventory_migration_stage stage
    ) numbered
    GROUP BY pms_property_id, room_type_id, quota, max_avail, run
"""

# Re-running has to be a no-op, and a run that died half way has to be able to
# finish: a range is only written if no rule of the general scope already
# covers any of its nights.
_INSERT_RULES = """
    CREATE TEMP TABLE pms_inventory_migration_inserted AS
    WITH inserted AS (
        INSERT INTO pms_inventory_rule (
            pms_property_id,
            room_type_id,
            date_from,
            date_to,
            quota,
            max_avail,
            active,
            create_uid,
            create_date,
            write_uid,
            write_date
        )
        SELECT
            migrated.pms_property_id,
            migrated.room_type_id,
            migrated.date_from,
            migrated.date_to,
            migrated.quota,
            migrated.max_avail,
            TRUE,
            %(uid)s,
            NOW() AT TIME ZONE 'UTC',
            %(uid)s,
            NOW() AT TIME ZONE 'UTC'
        FROM pms_inventory_migration_range migrated
        WHERE NOT EXISTS (
            SELECT 1
            FROM pms_inventory_rule existing
            WHERE existing.pms_property_id = migrated.pms_property_id
              AND existing.room_type_id = migrated.room_type_id
              AND existing.sale_channel_id IS NULL
              AND existing.agency_id IS NULL
              AND existing.date_from <= migrated.date_to
              AND existing.date_to >= migrated.date_from
        )
        RETURNING id
    )
    SELECT id FROM inserted
"""

# The resolution the runtime will answer with, rebuilt in SQL: every night
# covered by a rule of the general scope, and where several overlap, the one
# written last, which is how the resolver breaks the tie.
_EXPAND_RULES = """
    CREATE TEMP TABLE pms_inventory_migration_resolved AS
    SELECT DISTINCT ON (rule.pms_property_id, rule.room_type_id, night.date)
        rule.id AS rule_id,
        rule.pms_property_id,
        rule.room_type_id,
        night.date::date AS date,
        rule.quota,
        rule.max_avail
    FROM pms_inventory_rule rule
    CROSS JOIN LATERAL generate_series(
        rule.date_from, rule.date_to, INTERVAL '1 day'
    ) AS night(date)
    WHERE rule.active
      AND rule.sale_channel_id IS NULL
      AND rule.agency_id IS NULL
      AND rule.date_to >= %(cutoff)s
    ORDER BY
        rule.pms_property_id,
        rule.room_type_id,
        night.date,
        rule.write_date DESC,
        rule.id DESC
"""

# For every night the old model held a rule for, what the new model resolves
# has to be what the old columns said. Rebuilt from the legacy columns on one
# side and from the written ranges on the other. The quota is compared as a
# CAP, adding back to the old remainder what the scope had sold.
_CHECK_EQUIVALENCE = """
    SELECT
        night.pms_property_id,
        night.room_type_id,
        night.date,
        CASE
            WHEN night.quota > 0
            THEN night.quota + COALESCE(consumption.consumed, 0)
            ELSE night.quota
        END AS expected_quota,
        COALESCE(
            resolved.quota, COALESCE(room_type.default_quota, 0)
        ) AS actual_quota,
        night.max_avail AS expected_max_avail,
        COALESCE(
            resolved.max_avail,
            COALESCE(room_type.default_max_avail, 0)
        ) AS actual_max_avail
    FROM pms_inventory_migration_night night
    JOIN pms_room_type room_type ON room_type.id = night.room_type_id
    LEFT JOIN pms_inventory_migration_consumption consumption
        ON consumption.pms_property_id = night.pms_property_id
       AND consumption.room_type_id = night.room_type_id
       AND consumption.date = night.date
    LEFT JOIN pms_inventory_migration_resolved resolved
        ON resolved.pms_property_id = night.pms_property_id
       AND resolved.room_type_id = night.room_type_id
       AND resolved.date = night.date
    WHERE
        CASE
            WHEN night.quota > 0
            THEN night.quota + COALESCE(consumption.consumed, 0)
            ELSE night.quota
        END <> COALESCE(
            resolved.quota, COALESCE(room_type.default_quota, 0)
        )
        OR night.max_avail <> COALESCE(
            resolved.max_avail,
            COALESCE(room_type.default_max_avail, 0)
        )
"""

# The other direction: no rule written here may cover a night that had no rule
# at all, or the migration would be putting inventory on sale that was never
# configured.
_CHECK_NO_INVENTION = """
    SELECT
        resolved.pms_property_id,
        resolved.room_type_id,
        resolved.date
    FROM pms_inventory_migration_resolved resolved
    JOIN pms_inventory_migration_inserted inserted
        ON inserted.id = resolved.rule_id
    WHERE NOT EXISTS (
        SELECT 1
        FROM pms_inventory_migration_night night
        WHERE night.pms_property_id = resolved.pms_property_id
          AND night.room_type_id = resolved.room_type_id
          AND night.date = resolved.date
    )
"""

# Structural invariants of what was written. The INSERT goes around the Python
# constraints, so what the ORM would refuse has to be checked by hand: a
# later write from the interface over such a row would fail.
_CHECK_STRUCTURE = """
    SELECT 'range inverted or outside the migrated window' AS invariant,
           rule.id
    FROM pms_inventory_rule rule
    JOIN pms_inventory_migration_inserted inserted ON inserted.id = rule.id
    WHERE rule.date_to < rule.date_from
       OR rule.date_from < %(cutoff)s
    UNION ALL
    SELECT 'value below the no limit sentinel', rule.id
    FROM pms_inventory_rule rule
    JOIN pms_inventory_migration_inserted inserted ON inserted.id = rule.id
    WHERE rule.quota < -1 OR rule.max_avail < -1
    UNION ALL
    SELECT 'general scope rules overlapping each other', rule.id
    FROM pms_inventory_rule rule
    JOIN pms_inventory_migration_inserted inserted ON inserted.id = rule.id
    WHERE EXISTS (
        SELECT 1
        FROM pms_inventory_rule other
        WHERE other.id <> rule.id
          AND other.pms_property_id = rule.pms_property_id
          AND other.room_type_id = rule.room_type_id
          AND other.sale_channel_id IS NULL
          AND other.agency_id IS NULL
          AND other.date_from <= rule.date_to
          AND other.date_to >= rule.date_from
    )
"""

# A room type that is not available in the property it is limited in, which
# it reaches through the product template it delegates to. The old rows
# already carried it, so it is reported and not raised on: what it breaks is
# a future write over that rule, not this upgrade.
_REPORT_ROOM_TYPE_NOT_IN_PROPERTY = """
    WITH room_type_property AS (
        SELECT room_type.id AS room_type_id, rel.pms_property_id
        FROM pms_room_type room_type
        JOIN product_product product ON product.id = room_type.product_id
        JOIN product_template_pms_property_rel rel
            ON rel.product_tmpl_id = product.product_tmpl_id
    )
    SELECT
        rule.pms_property_id,
        rule.room_type_id,
        COUNT(*) AS rules
    FROM pms_inventory_rule rule
    JOIN pms_inventory_migration_inserted inserted ON inserted.id = rule.id
    WHERE EXISTS (
        SELECT 1
        FROM room_type_property scoped
        WHERE scoped.room_type_id = rule.room_type_id
    )
    AND NOT EXISTS (
        SELECT 1
        FROM room_type_property scoped
        WHERE scoped.room_type_id = rule.room_type_id
          AND scoped.pms_property_id = rule.pms_property_id
    )
    GROUP BY rule.pms_property_id, rule.room_type_id
    ORDER BY 3 DESC
"""

# Rows the old code could hold and a range cannot express: without a night
# there is nothing to write, and without a property or a room type there is
# no scope to write it in. Reported so that nothing is dropped in silence.
_REPORT_UNMIGRATABLE = """
    SELECT
        COUNT(*) FILTER (WHERE rule.date IS NULL) AS without_date,
        COUNT(*) FILTER (WHERE rule.pms_property_id IS NULL) AS without_property,
        COUNT(*) FILTER (WHERE rule.room_type_id IS NULL) AS without_room_type
    FROM pms_availability_plan_rule rule
    WHERE (
        rule.date IS NULL
        OR rule.pms_property_id IS NULL
        OR rule.room_type_id IS NULL
    )
    AND (rule.date IS NULL OR rule.date >= %(cutoff)s)
"""

# Where the plans disagreed the collapse cannot be transparent for all of
# them, since the minimum is what every rate gets from now on. A night closed
# by one plan while another had it open is worth telling apart from several
# finite limits coexisting.
_REPORT_DISAGREEMENT = """
    SELECT
        night.pms_property_id,
        night.room_type_id,
        COUNT(*) FILTER (
            WHERE night.quota = 0 AND night.quota_open_plans > 0
        ) AS quota_closed_by_one_plan,
        COUNT(*) FILTER (WHERE night.quota_values > 1) AS quota_disagreed,
        COUNT(*) FILTER (
            WHERE night.max_avail = 0 AND night.max_avail_open_plans > 0
        ) AS max_avail_closed_by_one_plan,
        COUNT(*) FILTER (WHERE night.max_avail_values > 1) AS max_avail_disagreed
    FROM pms_inventory_migration_night night
    GROUP BY night.pms_property_id, night.room_type_id
    HAVING COUNT(*) FILTER (
        WHERE night.quota_values > 1
           OR night.max_avail_values > 1
           OR (night.quota = 0 AND night.quota_open_plans > 0)
           OR (night.max_avail = 0 AND night.max_avail_open_plans > 0)
    ) > 0
    ORDER BY 3 DESC, 5 DESC, 4 DESC, 6 DESC
"""

# The nights where a rate that could be consulted in the property had no rule
# of its own. The old code answered those with the room type defaults, and the
# migrated rule replaces them, so this is the one place the collapse changes
# what a rate resolves to. The count that matters is the second one: the
# nights the defaults were closing.
_REPORT_MISSING_PLANS = """
    WITH reachable AS (
        SELECT DISTINCT
            property.id AS pms_property_id,
            pricelist.availability_plan_id AS availability_plan_id
        FROM pms_property property
        JOIN product_pricelist pricelist
            ON pricelist.availability_plan_id IS NOT NULL
        LEFT JOIN product_pricelist_pms_property_rel rel
            ON rel.product_pricelist_id = pricelist.id
        WHERE rel.pms_property_id IS NULL OR rel.pms_property_id = property.id
    ), missing AS (
        SELECT
            night.pms_property_id,
            night.room_type_id,
            night.date,
            night.quota,
            night.max_avail
        FROM pms_inventory_migration_night night
        JOIN reachable
            ON reachable.pms_property_id = night.pms_property_id
        WHERE NOT EXISTS (
            SELECT 1
            FROM pms_availability_plan_rule rule
            WHERE rule.pms_property_id = night.pms_property_id
              AND rule.room_type_id = night.room_type_id
              AND rule.date = night.date
              AND rule.availability_plan_id = reachable.availability_plan_id
        )
        GROUP BY 1, 2, 3, 4, 5
    )
    SELECT
        missing.pms_property_id,
        missing.room_type_id,
        COUNT(*) AS nights,
        COUNT(*) FILTER (
            WHERE COALESCE(room_type.default_quota, 0) <= 0
               OR COALESCE(room_type.default_max_avail, 0) <= 0
        ) AS nights_opening
    FROM missing
    JOIN pms_room_type room_type ON room_type.id = missing.room_type_id
    GROUP BY missing.pms_property_id, missing.room_type_id
    ORDER BY 4 DESC, 3 DESC
"""

# End-to-end against the stored ``plan_avail``, which the old model kept
# consistent and is the only witness of what the engine really answered.
# Reported and not raised on: it folds in ``real_avail``, which keeps moving
# with every reservation written while the upgrade runs.
_REPORT_PLAN_AVAIL = """
    WITH legacy AS (
        SELECT
            rule.pms_property_id,
            rule.room_type_id,
            rule.date,
            MIN(rule.{plan_avail}) AS plan_avail,
            MIN(COALESCE(rule.real_avail, 0)) AS real_avail,
            COUNT(DISTINCT COALESCE(rule.real_avail, 0)) AS real_avail_values
        FROM pms_availability_plan_rule rule
        WHERE rule.date >= %(cutoff)s
          AND rule.pms_property_id IS NOT NULL
          AND rule.room_type_id IS NOT NULL
        GROUP BY rule.pms_property_id, rule.room_type_id, rule.date
    ), resolution AS (
        SELECT
            legacy.plan_avail,
            legacy.real_avail,
            legacy.real_avail_values,
            COALESCE(
                resolved.quota,
                COALESCE(room_type.default_quota, 0)
            ) AS quota,
            COALESCE(
                resolved.max_avail,
                COALESCE(room_type.default_max_avail, 0)
            ) AS max_avail,
            COALESCE(consumption.consumed, 0) AS consumed
        FROM legacy
        JOIN pms_room_type room_type ON room_type.id = legacy.room_type_id
        LEFT JOIN pms_inventory_migration_consumption consumption
            ON consumption.pms_property_id = legacy.pms_property_id
           AND consumption.room_type_id = legacy.room_type_id
           AND consumption.date = legacy.date
        LEFT JOIN pms_inventory_migration_resolved resolved
            ON resolved.pms_property_id = legacy.pms_property_id
           AND resolved.room_type_id = legacy.room_type_id
           AND resolved.date = legacy.date
    ), bookable AS (
        SELECT
            resolution.plan_avail,
            resolution.real_avail,
            resolution.real_avail_values,
            LEAST(
                CASE
                    WHEN resolution.max_avail = -1 THEN {infinite}
                    ELSE resolution.max_avail
                END,
                CASE
                    WHEN resolution.quota = -1 THEN {infinite}
                    ELSE resolution.quota - resolution.consumed
                END
            ) AS cap
        FROM resolution
    )
    SELECT
        COUNT(*) AS nights,
        COUNT(*) FILTER (WHERE bookable.real_avail_values > 1) AS real_avail_split,
        COUNT(*) FILTER (
            WHERE bookable.plan_avail <> CASE
                WHEN bookable.cap = {infinite} THEN bookable.real_avail
                ELSE LEAST(bookable.real_avail, GREATEST(bookable.cap, 0))
            END
        ) AS mismatched
    FROM bookable
"""

_REPORTED_ROWS = 40


def _log_table(header, rows, columns):
    """Log an aggregated report, capped so that it stays readable."""
    _logger.info(
        "%s: %s row(s)%s\n%s",
        header,
        len(rows),
        "" if len(rows) <= _REPORTED_ROWS else " (first %s shown)" % _REPORTED_ROWS,
        "\n".join(
            [" | ".join(columns)]
            + [" | ".join(str(value) for value in row) for row in rows[:_REPORTED_ROWS]]
        ),
    )


@openupgrade.migrate()
def migrate(env, version):
    if not openupgrade.column_exists(
        env.cr, "pms_availability_plan_rule", LEGACY_QUOTA
    ):
        _logger.warning(
            "The inventory columns of the availability plan rules are not "
            "there, nothing to migrate."
        )
        return
    # Read once and reuse: the upgrade can cross midnight, and a cut-off that
    # moves half way through would leave the ranges and the checks disagreeing.
    env.cr.execute("SELECT CURRENT_DATE")
    cutoff = env.cr.fetchone()[0]
    params = {"cutoff": cutoff, "uid": env.uid}
    _logger.info("Migrating the commercial inventory of the nights from %s on", cutoff)

    openupgrade.logged_query(
        env.cr,
        _STAGE_NIGHTS.format(
            quota=_NORMALIZE.format(column="rule." + LEGACY_QUOTA),
            max_avail=_NORMALIZE.format(column="rule." + LEGACY_MAX_AVAIL),
            min_quota=_MIN_ACROSS_PLANS.format(
                value=_NORMALIZE.format(column="rule." + LEGACY_QUOTA)
            ),
            min_max_avail=_MIN_ACROSS_PLANS.format(
                value=_NORMALIZE.format(column="rule." + LEGACY_MAX_AVAIL)
            ),
        ),
        params,
    )
    openupgrade.logged_query(env.cr, _STAGE_CONSUMPTION, params)
    openupgrade.logged_query(env.cr, _STAGE_CAP)
    openupgrade.logged_query(env.cr, _DROP_REDUNDANT)
    openupgrade.logged_query(env.cr, _COLLAPSE_RANGES)
    openupgrade.logged_query(env.cr, _INSERT_RULES, params)
    openupgrade.logged_query(env.cr, _EXPAND_RULES, params)

    _report(env, params)
    _check(env, params)


def _report(env, params):
    env.cr.execute(_REPORT_UNMIGRATABLE, params)
    without_date, without_property, without_room_type = env.cr.fetchone()
    if without_date or without_property or without_room_type:
        _logger.warning(
            "Availability plan rules that cannot be expressed as an "
            "inventory range were left behind: %s without a date, %s without "
            "a property, %s without a room type.",
            without_date,
            without_property,
            without_room_type,
        )

    env.cr.execute(_REPORT_DISAGREEMENT, params)
    rows = env.cr.fetchall()
    if rows:
        _log_table(
            "Nights where the availability plans held a different inventory, "
            "so the minimum is what every rate resolves to from now on",
            rows,
            (
                "property",
                "room_type",
                "quota_closed_by_one_plan",
                "quota_disagreed",
                "max_avail_closed_by_one_plan",
                "max_avail_disagreed",
            ),
        )

    env.cr.execute(_REPORT_MISSING_PLANS, params)
    rows = env.cr.fetchall()
    if rows:
        _log_table(
            "Nights where a rate that can be consulted in the property had "
            "no rule of its own, which the old code answered with the room "
            "type defaults and the migrated rule now replaces",
            rows,
            ("property", "room_type", "nights", "nights_opening"),
        )

    env.cr.execute(_REPORT_ROOM_TYPE_NOT_IN_PROPERTY, params)
    rows = env.cr.fetchall()
    if rows:
        _log_table(
            "Inventory written for a room type that is not available in the "
            "property, which the availability plan rules already held and "
            "the interface will refuse to write again",
            rows,
            ("property", "room_type", "rules"),
        )

    env.cr.execute(
        _REPORT_PLAN_AVAIL.format(plan_avail=LEGACY_PLAN_AVAIL, infinite=INFINITE),
        params,
    )
    nights, real_avail_split, mismatched = env.cr.fetchone()
    log = _logger.warning if mismatched else _logger.info
    log(
        "Bookable availability against the stored plan_avail: %s of %s "
        "night(s) resolve to something else (%s of them hold more than one "
        "real availability for the same night, which the old model could "
        "not resolve consistently either).",
        mismatched,
        nights,
        real_avail_split,
    )


def _check(env, params):
    """Abort the upgrade if what was written does not resolve as it did.

    The migration runs inside the transaction of the update, so raising here
    rolls the whole thing back instead of leaving a half configured database.
    """
    failures = []
    for query, invariant, columns in (
        (
            _CHECK_EQUIVALENCE,
            "the resolved inventory is not the one the old columns held",
            (
                "property",
                "room_type",
                "date",
                "expected_quota",
                "actual_quota",
                "expected_max_avail",
                "actual_max_avail",
            ),
        ),
        (
            _CHECK_NO_INVENTION,
            "inventory was written for a night that had no rule",
            ("property", "room_type", "date"),
        ),
    ):
        env.cr.execute(query, params)
        rows = env.cr.fetchall()
        if rows:
            _log_table(f"FAILED: {invariant}", rows, columns)
            failures.append(f"{invariant} ({len(rows)} night(s))")

    env.cr.execute(_CHECK_STRUCTURE, params)
    rows = env.cr.fetchall()
    if rows:
        _log_table("FAILED: structural invariants", rows, ("invariant", "rule"))
        failures.append(f"{len(rows)} rule(s) break a structural invariant")

    if failures:
        raise ValueError(
            "The migration of the commercial inventory is not equivalent to "
            "the configuration it replaces, see the log for the detail: %s"
            % "; ".join(failures)
        )
