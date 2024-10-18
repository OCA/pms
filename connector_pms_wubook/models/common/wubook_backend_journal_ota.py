# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class WubookBackendJournalOTA(models.Model):
    _name = "wubook.backend.journal.ota"
    _description = "Journals Backend OTA Map to payment"
    _check_pms_properties_auto = True

    backend_id = fields.Many2one(
        comodel_name="channel.wubook.backend",
        required=True,
        ondelete="cascade",
    )

    pms_property_id = fields.Many2one(
        string="Property",
        related="backend_id.pms_property_id",
        store=True,
        readonly=True,
    )

    agency_id = fields.Many2one(
        string="OTA",
        comodel_name="res.partner",
        domain="[('id', 'in', allowed_agency_ids)]",
    )

    journal_id = fields.Many2one(
        string="Payment Journal",
        comodel_name="account.journal",
        domain="[('type', '=', 'bank')]",
        check_pms_properties=True,
    )

    allowed_agency_ids = fields.Many2many(
        string="Allowed Agencies",
        help="It contains all available otas for this backend",
        comodel_name="res.partner",
        compute="_compute_allowed_agency_ids",
    )

    @api.depends("backend_id")
    def _compute_allowed_agency_ids(self):
        for record in self:
            agency_ids = self.backend_id.backend_type_id.child_id.ota_ids.mapped(
                "agency_id.id"
            )
            if agency_ids:
                record.allowed_agency_ids = self.env["res.partner"].browse(agency_ids)
            else:
                record.allowed_agency_ids = False
