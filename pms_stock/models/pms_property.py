# Copyright (c) 2022 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    stock_location_id = fields.Many2one("stock.location", string="Inventory Location")
    stock_location_auto_created = fields.Boolean(
        string="Inventory Location Created Automatically",
        copy=False,
        readonly=True,
        help="Set when the inventory location was created by this module from "
        "the property name. Only such locations are renamed with the property.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        recs = super().create(vals_list)
        for rec in recs:
            if not rec.stock_location_id:
                rec._create_stock_location()
        return recs

    def write(self, vals):
        vals = dict(vals)
        if "stock_location_id" in vals:
            # The user picked another location: it is not ours to rename.
            vals.setdefault("stock_location_auto_created", False)
        res = super().write(vals)
        if "name" in vals:
            for rec in self:
                if not rec.stock_location_id:
                    rec._create_stock_location()
                elif rec.stock_location_auto_created:
                    rec.stock_location_id.name = rec.name
        return res

    def _create_stock_location(self):
        parent = self.env.ref("stock.stock_location_stock", raise_if_not_found=False)
        if not parent:
            return
        location = self.env["stock.location"].create(
            {
                "name": self.name,
                "location_id": parent.id,
                "usage": "internal",
            }
        )
        self.write(
            {
                "stock_location_id": location.id,
                "stock_location_auto_created": True,
            }
        )
