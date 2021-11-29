# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PmsPropertyReservation(models.Model):
    _name = "pms.property.reservation"
    _description = "Property Reservation"

    def _default_product_id(self):
        return self.env.ref(
            "pms_sale.product_product_reservation", raise_if_not_found=False
        )

    @api.depends("product_id")
    def _compute_price(self):
        for rec in self:
            if rec.product_id and rec.product_id.lst_price:
                rec.price = rec.product_id.lst_price or 0
            elif not rec.price:
                rec.price = 0

    name = fields.Char(string="Name", required=True)
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
        domain=[("reservation_ok", "=", True)],
        default=_default_product_id,
    )
    price = fields.Float(
        string="Price",
        compute="_compute_price",
        digits="Product Price",
        readonly=False,
        store=True,
    )
    property_id = fields.Many2one("pms.property", string="Property")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    def _get_reservation_multiline_description(self):
        """Compute a multiline description of this ticket. It is used when ticket
        description are necessary without having to encode it manually, like sales
        information."""
        return "%s\n%s" % (self.display_name, self.property_id.display_name)
