import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
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

    _logger.info("Recompute reservations sale channel ids...")
    env["pms.reservation"].search(
        [("reservation_type", "!=", "out")]
    )._compute_sale_channel_ids()
