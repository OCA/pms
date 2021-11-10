# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create


# REVIEW: move these two functions as a method of a mapper or binder
#         or in a tools library
def get_room_type(mapper, room_id):
    rt_binder = mapper.binder_for("channel.wubook.pms.room.type")
    room_type = rt_binder.to_internal(room_id, unwrap=True)
    assert room_type, (
        "room_id %s should have been imported in "
        "PmsRoomTypeImporter._import_dependencies" % (room_id,)
    )
    return room_type


def get_board_service_room_type(mapper, room_type, board):
    bd_binder = mapper.binder_for("channel.wubook.pms.board.service")
    board_service = bd_binder.to_internal(board, unwrap=True)
    assert board_service, (
        "board_service_id '%s' should've been imported in "
        "PmsRoomTypeImporter._import_dependencies or "
        "PmsFolioImporter._import_dependencies.\n" % (board,)
    )
    board_service_room_type_id = room_type.board_service_room_type_ids.filtered(
        lambda x: x.pms_board_service_id == board_service
    )
    if not board_service_room_type_id:
        raise ValidationError(
            _("The Board Service '%s' is not available in Room Type '%s'")
            % (board_service.default_code, room_type.default_code)
        )
    elif len(board_service_room_type_id) > 1:
        raise ValidationError(
            _("The Board Service '%s' is duplicated in Room Type '%s'")
            % (board_service.default_code, room_type.default_code)
        )
    return board_service_room_type_id


class ChannelWubookPmsReservationMapperImport(Component):
    _name = "channel.wubook.pms.reservation.mapper.import"
    _inherit = "channel.wubook.mapper.import"

    _apply_on = "channel.wubook.pms.reservation"

    direct = [("occupancy", "adults")]

    children = [
        ("lines", "reservation_line_ids", "channel.wubook.pms.reservation.line"),
    ]

    @only_create
    @mapping
    def pms_property_id(self, record):
        return {"pms_property_id": self.backend_record.pms_property_id.id}

    @mapping
    def room_type_id(self, record):
        return {"room_type_id": get_room_type(self, record["room_id"]).id}

    @mapping
    def room_type_board_service(self, record):
        if record["board"]:
            room_type = get_room_type(self, record["room_id"])
            return {
                "board_service_room_id": get_board_service_room_type(
                    self, room_type, record["board"]
                ).id
            }

    @mapping
    def ota_reservation_code(self, record):
        if record["ota_reservation_code"]:
            return {"ota_reservation_code": record["ota_reservation_code"]}

    @mapping
    def dates(self, record):
        if record["arrival_hour"]:
            return {
                "arrival_hour": record["arrival_hour"],
            }

    @mapping
    def requests(self, record):
        return {
            "partner_requests": record["customer_notes"],
        }

    @mapping
    def pricelist_id(self, record):
        pricelist_id = False
        if record["rate_id"]:
            binder = self.binder_for("channel.wubook.product.pricelist")
            pricelist = binder.to_internal(record["rate_id"], unwrap=True)
            assert pricelist, (
                "rate_id %s should have been imported in "
                "ProductPricelistImporter._import_dependencies" % (record["rate_id"],)
            )
            pricelist_id = pricelist.id

            if pricelist_id:
                return {"pricelist_id": pricelist_id}


class ChannelWubookPmsReservationChildMapperImport(Component):
    _name = "channel.wubook.pms.reservation.child.mapper.import"
    _inherit = "channel.wubook.child.mapper.import"
    _apply_on = "channel.wubook.pms.reservation.line"
