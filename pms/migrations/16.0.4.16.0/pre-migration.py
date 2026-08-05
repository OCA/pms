import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# The hour fields stored as Char only accept a zero-padded 24h "HH:MM" string
# now. Values stored while the check accepted anything strptime("%H:%M")
# parsed are normalized here, or their records cannot be written again.
_NORMALIZE_PROPERTY_HOURS = """
    UPDATE pms_property
    SET default_arrival_hour = CASE
            WHEN default_arrival_hour = '24:00' THEN '23:59'
            WHEN default_arrival_hour ~ '^[0-9]{1,2}:[0-9]{1,2}$'
                THEN lpad(split_part(default_arrival_hour, ':', 1), 2, '0')
                     || ':'
                     || lpad(split_part(default_arrival_hour, ':', 2), 2, '0')
            ELSE default_arrival_hour
        END,
        default_departure_hour = CASE
            WHEN default_departure_hour = '24:00' THEN '23:59'
            WHEN default_departure_hour ~ '^[0-9]{1,2}:[0-9]{1,2}$'
                THEN lpad(split_part(default_departure_hour, ':', 1), 2, '0')
                     || ':'
                     || lpad(split_part(default_departure_hour, ':', 2), 2, '0')
            ELSE default_departure_hour
        END
    WHERE default_arrival_hour !~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'
       OR default_departure_hour !~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'
"""

_NORMALIZE_RESERVATION_HOURS = """
    UPDATE pms_reservation
    SET arrival_hour = CASE
            WHEN arrival_hour = '24:00' THEN '23:59'
            WHEN arrival_hour ~ '^[0-9]{1,2}:[0-9]{1,2}$'
                THEN lpad(split_part(arrival_hour, ':', 1), 2, '0')
                     || ':'
                     || lpad(split_part(arrival_hour, ':', 2), 2, '0')
            ELSE arrival_hour
        END,
        departure_hour = CASE
            WHEN departure_hour = '24:00' THEN '23:59'
            WHEN departure_hour ~ '^[0-9]{1,2}:[0-9]{1,2}$'
                THEN lpad(split_part(departure_hour, ':', 1), 2, '0')
                     || ':'
                     || lpad(split_part(departure_hour, ':', 2), 2, '0')
            ELSE departure_hour
        END
    WHERE arrival_hour !~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'
       OR departure_hour !~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'
"""

# The property hours are required now.
_FILL_EMPTY_PROPERTY_HOURS = """
    UPDATE pms_property
    SET default_arrival_hour = COALESCE(NULLIF(default_arrival_hour, ''), '14:00'),
        default_departure_hour = COALESCE(NULLIF(default_departure_hour, ''), '12:00')
    WHERE default_arrival_hour IS NULL OR default_arrival_hour = ''
       OR default_departure_hour IS NULL OR default_departure_hour = ''
"""

_SELECT_NOT_NORMALIZED = """
    SELECT 'pms_property.default_arrival_hour', id, default_arrival_hour
    FROM pms_property
    WHERE default_arrival_hour !~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'
    UNION ALL
    SELECT 'pms_property.default_departure_hour', id, default_departure_hour
    FROM pms_property
    WHERE default_departure_hour !~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'
    UNION ALL
    SELECT 'pms_reservation.arrival_hour', id, arrival_hour
    FROM pms_reservation
    WHERE arrival_hour IS NOT NULL
      AND arrival_hour !~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'
    UNION ALL
    SELECT 'pms_reservation.departure_hour', id, departure_hour
    FROM pms_reservation
    WHERE departure_hour IS NOT NULL
      AND departure_hour !~ '^([01][0-9]|2[0-3]):[0-5][0-9]$'
"""


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(env.cr, _NORMALIZE_PROPERTY_HOURS)
    openupgrade.logged_query(env.cr, _NORMALIZE_RESERVATION_HOURS)
    openupgrade.logged_query(env.cr, _FILL_EMPTY_PROPERTY_HOURS)
    env.cr.execute(_SELECT_NOT_NORMALIZED)
    not_normalized = env.cr.fetchall()
    if not_normalized:
        _logger.warning(
            "%s hour value(s) are not an hour and were left untouched, "
            "they need a manual review: %s",
            len(not_normalized),
            not_normalized,
        )
