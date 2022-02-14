# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsPropertyReservation(models.Model):
    _inherit = "pms.property.reservation"

    is_guesty_price = fields.Boolean()

    @api.constrains("property_id", "is_guesty_price")
    def _check_single_guesty_price(self):
        if self.is_guesty_price:
            check = self.search(
                [
                    ("property_id", "=", self.property_id.id),
                    ("is_guesty_price", "=", True),
                    ("id", "!=", self.id),
                ]
            )

            if check:
                raise ValidationError(_("Multiple guesty prices are not allowed"))
