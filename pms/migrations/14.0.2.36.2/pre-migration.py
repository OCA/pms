import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

_field_renames = [
    ("pms.folio", "pms_folio", "channel_type_id", "sale_channel_origin_id"),
    ("pms.reservation", "pms_reservation", "channel_type_id", "sale_channel_origin_id"),
]
_field_creates = [
    (
        "sale_channel_id",
        "pms.reservation.line",
        "pms_reservation_line",
        "many2one",
        "integer",
        "pms",
    ),
    (
        "sale_channel_origin_id",
        "pms.service",
        "pms_service",
        "many2one",
        "integer",
        "pms",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, _field_renames)
    openupgrade.add_fields(env, _field_creates)
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE pms_reservation_line rl
        SET sale_channel_id = r.sale_channel_origin_id
        FROM pms_reservation r
        WHERE r.id = rl.reservation_id
        """,
    )

    openupgrade.logged_query(
        env.cr,
        """
        UPDATE pms_service ser
        SET sale_channel_origin_id = fol.sale_channel_origin_id
        FROM pms_folio fol
        WHERE fol.id = ser.folio_id
        """,
    )
