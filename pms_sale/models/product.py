# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    reservation_ok = fields.Boolean(string="Reservation")

    @api.onchange("reservation_ok")
    def _onchange_reservation_ok(self):
        if self.reservation_ok:
            self.type = "service"


class Product(models.Model):
    _inherit = "product.product"

    @api.onchange("reservation_ok")
    def _onchange_reservation_ok(self):
        if self.reservation_ok:
            self.type = "service"
