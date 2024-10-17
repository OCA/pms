import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    _logger.info("Recompute reservations sale channel ids...")
    env["pms.reservation"].search(
        [("reservation_type", "!=", "out")]
    )._compute_sale_channel_ids()
