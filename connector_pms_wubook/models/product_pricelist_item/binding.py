# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ChannelWubookProductPricelistItemBinding(models.Model):
    _name = "channel.wubook.product.pricelist.item"
    _inherit = "channel.wubook.binding"
    _inherits = {"product.pricelist.item": "odoo_id"}

    external_id = fields.Char(string="External ID")

    odoo_id = fields.Many2one(
        comodel_name="product.pricelist.item",
        string="Odoo ID",
        required=True,
        ondelete="cascade",
    )

    channel_wubook_pricelist_id = fields.Many2one(
        comodel_name="channel.wubook.product.pricelist",
        string="Wubook Pricelist ID",
        required=True,
        ondelete="cascade",
    )

    @api.model
    def create(self, vals):
        channel_wubook_pricelist_id = vals.get("channel_wubook_pricelist_id")
        if channel_wubook_pricelist_id:
            binding = self.channel_wubook_pricelist_id.browse(
                channel_wubook_pricelist_id
            )
            vals["pricelist_id"] = binding.odoo_id.id
        else:
            # TODO: put this code on mapper???? Is it possible??
            backend = self.backend_id.browse(vals["backend_id"])
            with backend.work_on(self.channel_wubook_pricelist_id._name) as work:
                binder = work.component(usage="binder")
            binding = binder.wrap_record(
                self.odoo_id.browse(vals["odoo_id"]).pricelist_id
            )
            vals["channel_wubook_pricelist_id"] = binding.id
        binding = super().create(vals)
        return binding
