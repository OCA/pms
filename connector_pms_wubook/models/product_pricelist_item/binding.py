# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ChannelWubookProductPricelistItemBinding(models.AbstractModel):
    _name = "channel.wubook.product.pricelist.item"
    _inherit = "channel.wubook.binding"
    _inherits = {"product.pricelist.item": "odoo_id"}

    odoo_id = fields.Many2one(
        comodel_name="product.pricelist.item",
        string="Odoo ID",
        required=True,
        ondelete="cascade",
    )
