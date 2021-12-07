# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector_pms_wubook.models.pms_reservation.mapper_import import (
    get_board_service_room_type,
    get_room_type,
)


class ChannelWubookPmsReservationLineMapperImport(Component):
    _name = "channel.wubook.pms.reservation.line.mapper.import"
    _inherit = "channel.wubook.mapper.import"

    _apply_on = "channel.wubook.pms.reservation.line"

    direct = [
        ("day", "date"),
    ]

    @mapping
    def price(self, record):
        price = record["price"]
        if record["board"] and record["board_included"]:
            room_type = get_room_type(self, record["room_id"])
            board_service_room = get_board_service_room_type(
                self, room_type, record["board"]
            )
            price -= board_service_room.amount * record["occupancy"]
        return {"price": price}
