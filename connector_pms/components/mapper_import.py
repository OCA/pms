# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class ChannelMapperImport(AbstractComponent):
    _name = "channel.mapper.import"
    _inherit = "base.import.mapper"


class ChannelChildMapperImport(AbstractComponent):
    _name = "channel.child.mapper.import"
    _inherit = "base.map.child.import"

    def get_all_items(self, mapper, items, parent, to_attr, options):
        mapped = []
        for item in items:
            map_record = mapper.map_record(item, parent=parent)
            if self.skip_item(map_record):
                continue
            item_values = self.get_item_values(map_record, to_attr, options)
            if item_values:
                mapped.append(item_values)
        return mapped

    def get_items(self, items, parent, to_attr, options):
        mapper = self._child_mapper()
        mapped = self.get_all_items(mapper, items, parent, to_attr, options)
        return self.format_items(mapped)
