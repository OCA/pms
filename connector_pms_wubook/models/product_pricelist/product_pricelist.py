# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    channel_wubook_bind_ids = fields.One2many(
        comodel_name="channel.wubook.product.pricelist",
        inverse_name="odoo_id",
        string="Channel Wubook PMS Bindings",
    )

    wubook_plan_type = fields.Selection(
        selection=[("virtual", "Virtual"), ("standard", "Standard")],
        readonly=True,
        store=True,
        compute="_compute_wubook_plan_type",
    )

    @api.depends("item_ids.wubook_item_type")
    def _compute_wubook_plan_type(self):
        for rec in self:
            if rec.pricelist_type == "daily":
                item_types = rec.item_ids.mapped("wubook_item_type")
                # if 'virtual' in item_types:
                #     raise ValidationError(_("A daily pricelist cannot have any 'Virtual' item"))
                if "standard" in item_types:
                    rec.wubook_plan_type = "standard"
                else:
                    rec.wubook_plan_type = False
            else:
                virtual_items = rec.item_ids.filtered(
                    lambda x: x.wubook_item_type == "virtual"
                )
                if len(virtual_items) == 1:
                    rec.wubook_plan_type = "virtual"
                else:
                    rec.wubook_plan_type = False
                # item_types = set(record.item_ids.mapped('wubook_item_type'))
                # if item_types == {'standard'}:
                #     raise ValidationError(_("Non Daily pricelist cannot have Wubook standard items"))
                # else:
                #     if {'virtual', 'standard'}.issubset(item_types):
                #         raise ValidationError(_("Mixed virtual and standard items not supported"))
                #     else:
                #         virtual_items = record.item_ids.filtered(lambda x: x.wubook_item_type == 'virtual')
                #         if len(virtual_items) == 1:
                #             return {'type': 'virtual'}
                #         elif len(virtual_items) > 1:
                #             raise ValidationError(_("Multiple virtual items not supported"))
