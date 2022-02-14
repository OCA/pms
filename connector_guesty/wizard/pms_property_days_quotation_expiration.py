# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_log = logging.getLogger(__name__)


class PmsPropertyDaysQuotationExpiration(models.TransientModel):
    _name = "pms.property.days.quotation.expiration"
    _description = "PMS Property Days Quotation Expiration"

    property_ids = fields.Many2many(string="Properties", comodel_name="pms.property")
    days_quotation_expiration = fields.Integer(string="Days to quotation expiration", default=1)

    @api.constrains("days_quotation_expiration")
    def check_days_quotation_expiration(self):
        if self.days_quotation_expiration > 2:
            raise ValidationError(_("Maximum of  2 days for 'Days to quotation expiration'"))

    @api.onchange("days_quotation_expiration")
    def _onchange_days_quotation_expiration(self):
        self.check_days_quotation_expiration()

    def update_property_days_quotation_expiration(self):
        for property_id in self.property_ids:
            property_id.write({'days_quotation_expiration': self.days_quotation_expiration})
