from datetime import datetime

from odoo import _
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsRoomService(Component):
    _inherit = "base.rest.service"
    _name = "pms.room.service"
    _usage = "rooms"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.room.search.param"),
        output_param=Datamodel("pms.room.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_rooms(self, room_search_param):
        domain = []
        if room_search_param.name:
            domain.append(("name", "like", room_search_param.name))
        if room_search_param.pmsPropertyId:
            domain.append(("pms_property_id", "=", room_search_param.pmsPropertyId))
        if (
            room_search_param.availabilityFrom
            and room_search_param.availabilityTo
            and room_search_param.pmsPropertyId
        ):
            date_from = datetime.strptime(
                room_search_param.availabilityFrom, "%Y-%m-%d"
            ).date()
            date_to = datetime.strptime(
                room_search_param.availabilityTo, "%Y-%m-%d"
            ).date()
            pms_property = self.env["pms.property"].browse(
                room_search_param.pmsPropertyId
            )
            if not room_search_param.pricelistId:
                pms_property = self.env["pms.property"].browse(
                    room_search_param.pmsPropertyId
                )
                pms_property = pms_property.with_context(
                    checkin=date_from,
                    checkout=date_to,
                    room_type_id=False,  # Allows to choose any available room
                    current_lines=room_search_param.currentLines,
                    real_avail=True,
                )
            else:
                pms_property = pms_property.with_context(
                    checkin=date_from,
                    checkout=date_to,
                    room_type_id=False,  # Allows to choose any available room
                    current_lines=room_search_param.currentLines,
                    pricelist_id=room_search_param.pricelistId,
                    real_avail=True,
                )
            domain.append(("id", "in", pms_property.free_room_ids.ids))
        result_rooms = []
        PmsRoomInfo = self.env.datamodels["pms.room.info"]
        for room in (
            self.env["pms.room"]
            .search(
                domain,
            )
            .sorted("capacity")
        ):

            result_rooms.append(
                PmsRoomInfo(
                    id=room.id,
                    name=room.name,
                    roomTypeId=room.room_type_id,
                    capacity=room.capacity,
                    shortName=room.short_name,
                    roomTypeClassId=room.room_type_id.class_id,
                    ubicationId=room.ubication_id,
                    extraBedsAllowed=room.extra_beds_allowed,
                    roomAmenityIds=room.room_amenity_ids.ids
                    if room.room_amenity_ids
                    else None,
                )
            )
        return result_rooms

    @restapi.method(
        [
            (
                [
                    "/<int:room_id>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.room.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_room(self, room_id):
        room = self.env["pms.room"].search([("id", "=", room_id)])
        if room:
            PmsRoomInfo = self.env.datamodels["pms.room.info"]
            return PmsRoomInfo(
                id=room.id,
                name=room.name,
                roomTypeId=room.room_type_id,
                capacity=room.capacity,
                shortName=room.short_name,
                extraBedsAllowed=room.extra_beds_allowed,
            )
        else:
            raise MissingError(_("Room not found"))

    @restapi.method(
        [
            (
                [
                    "/p/<int:room_id>",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.room.info"),
        auth="jwt_api_pms",
    )
    def update_room(self, room_id, pms_room_info_data):
        room = self.env["pms.room"].search([("id", "=", room_id)])
        if room:
            room.name = pms_room_info_data.name
        else:
            raise MissingError(_("Room not found"))

    @restapi.method(
        [
            (
                [
                    "/<int:room_id>",
                ],
                "DELETE",
            )
        ],
        auth="jwt_api_pms",
    )
    def delete_room(self, room_id):
        # esto tb podría ser con un browse
        room = self.env["pms.room"].search([("id", "=", room_id)])
        if room:
            room.active = False
        else:
            raise MissingError(_("Room not found"))

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.room.info"),
        auth="jwt_api_pms",
    )
    def create_room(self, pms_room_info_param):
        room = self.env["pms.room"].create(
            {
                "name": pms_room_info_param.name,
                "room_type_id": pms_room_info_param.roomTypeId,
                "capacity": pms_room_info_param.capacity,
                "short_name": pms_room_info_param.shortName,
            }
        )
        return room.id
