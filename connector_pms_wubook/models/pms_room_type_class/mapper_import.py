# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create


class ChannelWubookPmsRoomTypeClassMapperImport(Component):
    _name = "channel.wubook.pms.room.type.class.mapper.import"
    _inherit = "channel.wubook.mapper.import"

    _apply_on = "channel.wubook.pms.room.type.class"

    direct = [
        ("name", "name"),
        ("shortname", "default_code"),
    ]

    @only_create
    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}

    @mapping
    def property_ids(self, record):
        binding = self.options.get("binding")
        has_pms_properties = binding and bool(binding.pms_property_ids)
        if self.options.for_create or has_pms_properties:
            return {
                "pms_property_ids": [(4, self.backend_record.pms_property_id.id, 0)]
            }
