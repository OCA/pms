# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create


class ChannelWubookPmsRoomTypeMapperImport(Component):
    _name = "channel.wubook.pms.room.type.mapper.import"
    _inherit = "channel.wubook.mapper.import"

    _apply_on = "channel.wubook.pms.room.type"

    direct = [
        ("name", "name"),
        ("occupancy", "occupancy"),
        ("availability", "default_availability"),
        ("price", "list_price"),
        ("min_price", "min_price"),
        ("max_price", "max_price"),
    ]

    children = [
        (
            "boards",
            "board_service_room_type_ids",
            "channel.wubook.pms.room.type.board.service",
        ),
    ]

    @only_create
    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}

    @only_create
    @mapping
    def default_code(self, record):
        return {
            "default_code": record["shortname"],
        }

    @mapping
    def class_id(self, record):
        binder = self.binder_for("channel.wubook.pms.room.type.class")
        room_type_class = binder.to_internal(record["rtype"], unwrap=True)
        return {
            "class_id": room_type_class.id,
        }

    @mapping
    def property_ids(self, record):
        binding = self.options.get("binding")
        has_pms_properties = binding and bool(binding.pms_property_ids)
        if self.options.for_create or has_pms_properties:
            return {
                "pms_property_ids": [(4, self.backend_record.pms_property_id.id, 0)]
            }


# TODO: import room type with board service changes

# class ChannelWubookPmsRoomTypeBoardServiceChildMapperImport(Component):
#     _name = "channel.wubook.pms.room.type.board.service.child.mapper.import"
#     _inherit = "channel.wubook.child.mapper.import"
#     _apply_on = "channel.wubook.pms.room.type.board.service"
#
#     def get_item_values(self, map_record, to_attr, options):
#         values = super().get_item_values(map_record, to_attr, options)
#         options.get("binding")
#         return values
