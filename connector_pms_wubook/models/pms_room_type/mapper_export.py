# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class ChannelWubookPmsRoomTypeMapperExport(Component):
    _name = "channel.wubook.pms.room.type.mapper.export"
    _inherit = "channel.wubook.mapper.export"

    _apply_on = "channel.wubook.pms.room.type"

    direct = [
        ("name", "name"),
        ("occupancy", "occupancy"),
        ("list_price", "price"),
        ("default_code", "shortname"),
        ("min_price", "min_price"),
        ("max_price", "max_price"),
        ("default_availability", "availability"),
    ]

    children = [
        (
            "board_service_room_type_ids",
            "boards",
            "channel.wubook.pms.room.type.board.service",
        ),
    ]

    @mapping
    def default_board_service(self, record):
        default_board_service = record.board_service_room_type_ids.filtered(
            lambda x: x.by_default
        ).mapped("pms_board_service_id")
        if not default_board_service:
            return {"board": "nb"}
        if len(default_board_service) != 1:
            raise ValidationError(
                _(
                    "Room type %s: The number of default Board Services must be exactly 1"
                )
                % record.name
            )

        bs_binder = self.binder_for("channel.wubook.pms.board.service")
        external_id = bs_binder.to_external(default_board_service, wrap=True)
        if not external_id:
            raise ValidationError(
                _(
                    "External record of Board Service [%s] %s does not exists. "
                    "It should be exported in _export_dependencies"
                )
                % (default_board_service.default_code, default_board_service.name)
            )
        return {"board": external_id}

    @mapping
    def room_type_class(self, record):
        room_class = record.class_id
        rc_binder = self.binder_for("channel.wubook.pms.room.type.class")
        external_id = rc_binder.to_external(room_class, wrap=True)
        if not external_id:
            raise ValidationError(
                _(
                    "External record of Room Class [%s] %s does not exists. "
                    "It should be exported in _export_dependencies"
                )
                % (room_class.default_code, room_class.name)
            )
        return {"rtype": external_id}

    @mapping
    def woodoo(self, record):
        return {"woodoo": 0}


class ChannelWubookPmsRoomTypeBoardServiceChildMapperExport(Component):
    _name = "channel.wubook.pms.room.type.board.service.child.mapper.export"
    _inherit = "channel.wubook.child.mapper.export"
    _apply_on = "channel.wubook.pms.room.type.board.service"

    def format_items(self, items_values):
        # avoid adding many2one crud operation codes
        values = {}
        for item in items_values:
            values.update(item)
        return values
