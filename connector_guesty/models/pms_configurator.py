# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, api, models
from odoo.exceptions import ValidationError

_log = logging.getLogger(__name__)


class PmsConfigurator(models.TransientModel):
    _inherit = "pms.configurator"

    @api.model
    def create(self, values):
        res = super().create(values)
        res.guesty_validate_currency()
        return res

    def write(self, values):
        res = super().write(values)
        self.guesty_validate_currency()
        return res

    def guesty_validate_currency(self):
        if self.property_id.guesty_id:
            guesty_price = self.property_id.reservation_ids.filtered(
                lambda s: s.is_guesty_price
            )
            if guesty_price and guesty_price.currency_id.id != self.currency_id.id:
                raise ValidationError(
                    _(
                        "The SO currency are not available for this property/listing. "
                        "Please change the currency on the SO"
                    )
                )
