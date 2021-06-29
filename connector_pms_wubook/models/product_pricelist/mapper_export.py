# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create


class ChannelWubookProductPricelistMapperExport(Component):
    _name = "channel.wubook.product.pricelist.mapper.export"
    _inherit = "channel.wubook.mapper.export"

    _apply_on = "channel.wubook.product.pricelist"

    direct = [
        ("name", "name"),
    ]

    children = [("item_ids", "items", "channel.wubook.product.pricelist.item")]

    @only_create
    @mapping
    def pricelist_type(self, record):
        if record.pricelist_type != "daily":
            raise ValidationError(_("Only 'Daily' pricelists are supported"))
        return {"daily": 1}

    @mapping
    def pricelist_plan_type(self, record):
        return {"type": record.wubook_plan_type}


class ChannelWubookProductPricelistChildMapperExport(Component):
    _name = "channel.wubook.product.pricelist.child.mapper.export"
    _inherit = "channel.wubook.child.mapper.export"

    _apply_on = "channel.wubook.product.pricelist.item"

    def skip_item(self, map_record):
        return (
            not map_record.source.wubook_item_type
            or map_record.parent.source.wubook_plan_type
            != map_record.source.wubook_item_type
        ) or (
            map_record.source.pms_property_ids
            and self.backend_record.pms_property_id
            not in map_record.source.pms_property_ids
        )
