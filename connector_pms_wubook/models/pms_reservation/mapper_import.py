# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create


class ChannelWubookPmsReservationMapperImport(Component):
    _name = "channel.wubook.pms.reservation.mapper.import"
    _inherit = "channel.wubook.mapper.import"

    _apply_on = "channel.wubook.pms.reservation"

    children = [
        ("lines", "reservation_line_ids", "channel.wubook.pms.reservation.line"),
    ]

    def _get_room_type(self, room_id):
        rt_binder = self.binder_for("channel.wubook.pms.room.type")
        room_type = rt_binder.to_internal(room_id, unwrap=True)
        assert room_type, (
            "room_id %s should have been imported in "
            "PmsRoomTypeImporter._import_dependencies" % (room_id,)
        )
        return room_type

    @only_create
    @mapping
    def pms_property_id(self, record):
        return {"pms_property_id": self.backend_record.pms_property_id.id}

    @mapping
    def room_type_id(self, record):
        return {"room_type_id": self._get_room_type(record["room_id"]).id}

    @mapping
    def room_type_board_service(self, record):
        if record["board"]:
            room_type = self._get_room_type(record["room_id"])
            bd_binder = self.binder_for("channel.wubook.pms.board.service")
            board_service = bd_binder.to_internal(record["board"], unwrap=True)
            assert board_service, (
                "board_service_id '%s' should've been imported in "
                "PmsRoomTypeImporter._import_dependencies or "
                "PmsFolioImporter._import_dependencies.\n"
                # "If not, probably the Board Service '%s' is not defined "
                # "as a Board Service of Room Type '%s' and/or although the "
                # "Board service exists in the PMS it has no Binding so it's "
                # "not linked to the Backend."
                % (record["board"], record["board"], room_type.default_code)
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
            return {"board_service_room_id": board_service_room_type_id.id}

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
