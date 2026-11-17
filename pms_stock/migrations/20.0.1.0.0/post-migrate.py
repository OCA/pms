# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Flag the inventory locations created by this module before 20.0.

    Until 20.0 a property rename renamed whatever location was linked to it.
    From 20.0 on only locations created by this module are renamed, so flag
    the ones whose name still tracks the property name.
    """
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    property_ids = env["pms.property"].search([("stock_location_id", "!=", False)])
    flagged_ids = property_ids.filtered(
        lambda property_id: property_id.stock_location_id.name == property_id.name
    )
    flagged_ids.write({"stock_location_auto_created": True})
    _logger.info("pms_stock: flagged %s auto-created locations", len(flagged_ids))
