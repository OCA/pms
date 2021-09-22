# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class ChannelWubookProductPricelistDelayedBatchExporter(Component):
    _name = "channel.wubook.product.pricelist.delayed.batch.exporter"
    _inherit = "channel.wubook.delayed.batch.exporter"

    _apply_on = "channel.wubook.product.pricelist"


class ChannelWubookProductPricelistDirectBatchExporter(Component):
    _name = "channel.wubook.product.pricelist.direct.batch.exporter"
    _inherit = "channel.wubook.direct.batch.exporter"

    _apply_on = "channel.wubook.product.pricelist"


class ChannelWubookProductPricelistExporter(Component):
    _name = "channel.wubook.product.pricelist.exporter"
    _inherit = "channel.wubook.exporter"

    _apply_on = "channel.wubook.product.pricelist"

    def _export_dependencies(self):
        for room_type in self.binding.item_ids.filtered(
            lambda x: x.wubook_item_type == "standard"
        ).mapped("product_id.room_type_id"):
            self._export_dependency(room_type, "channel.wubook.pms.room.type")

        for pricelist in self.binding.item_ids.filtered(
            lambda x: x.wubook_item_type == "virtual"
        ).mapped("base_pricelist_id"):
            self._export_dependency(pricelist, "channel.wubook.product.pricelist")
