# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ChannelWubookBackendTypeOTA(models.Model):
    _name = "channel.wubook.backend.type.ota"
    _description = "Channel Wubook PMS Backend OTA Map"

    backend_type_id = fields.Many2one(
        comodel_name="channel.wubook.backend.type",
        required=True,
        ondelete="cascade",
    )

    wubook_ota = fields.Integer(
        string="Wubook OTA ID",
        required=True,
    )

    agency_id = fields.Many2one(
        comodel_name="res.partner",
        domain="[('is_agency', '=', True)]",
        string="Agency",
    )

    _sql_constraints = [
        (
            "uniq",
            "unique(backend_type_id,wubook_ota,agency_id)",
            "Wubook OTA ID and Agency already used in another map line",
        ),
        (
            "board_service_uniq",
            "unique(backend_type_id,wubook_ota)",
            "Wubook OTa ID already used in another map line",
        ),
        (
            "board_service_shortname_uniq",
            "unique(backend_type_id,agency_id)",
            "Agency already used in another map line",
        ),
    ]
