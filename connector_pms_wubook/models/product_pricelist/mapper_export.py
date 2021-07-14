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

    children = [
        ("channel_wubook_item_ids", "items", "channel.wubook.product.pricelist.item")
    ]

    @only_create
    @mapping
    def pricelist_type(self, record):
        if record.pricelist_type != "daily":
            raise ValidationError(_("Only 'Daily' pricelists are supported"))
        return {"daily": 1}

    @mapping
    def pricelist_plan_type(self, record):
        return {"type": record.wubook_plan_type}


class ChannelWubookProductPricelistChildBinderMapperExport(Component):
    _name = "channel.wubook.product.pricelist.child.binder.mapper.export"
    _inherit = "channel.wubook.child.binder.mapper.export"

    _apply_on = "channel.wubook.product.pricelist.item"

    def skip_item(self, map_record):
        return (
            (
                not map_record.source.wubook_item_type
                or map_record.parent.source.wubook_plan_type
                != map_record.source.wubook_item_type
            )
            or (
                map_record.source.pms_property_ids
                and self.backend_record.pms_property_id
                not in map_record.source.pms_property_ids
            )
            or map_record.source.synced_export
        )

    def get_all_items(self, mapper, items, parent, to_attr, options):
        # TODO: this is always the same on every child binder mapper
        #   except 'rule_ids' try to move it to the parent
        bindings = items.filtered(lambda x: x.backend_id == self.backend_record)
        new_bindings = parent.source["item_ids"].filtered(
            lambda x: self.backend_record not in x.channel_wubook_bind_ids.backend_id
        )
        items = (
            items.browse(
                [self.binder_for().wrap_record(x, force=True).id for x in new_bindings]
            )
            | bindings
        )
        mapper = super().get_all_items(mapper, items, parent, to_attr, options)
        return mapper
