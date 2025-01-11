from datetime import datetime

from odoo import _
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

from ..pms_api_rest_utils import pms_api_check_access


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
            pms_property = (
                self.env["pms.property"].sudo().browse(room_search_param.pmsPropertyId)
            )
            pms_api_check_access(user=self.env.user, records=pms_property)
            if not room_search_param.pricelistId:
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
        rooms = self.env["pms.room"].sudo().search(domain).sorted("sequence")
        pms_api_check_access(user=self.env.user, records=rooms)
        for room in rooms:
            # TODO: avoid, change short_name,
            # set code amenities like a tag in room calendar name?
            short_name = room.short_name
            # if room.room_amenity_ids:
            #     for amenity in room.room_amenity_ids:
            #         if amenity.is_add_code_room_name:
            #             short_name += "%s" % amenity.default_code
            result_rooms.append(
                PmsRoomInfo(
                    id=room.id,
                    name=room.display_name,
                    roomTypeId=room.room_type_id,
                    capacity=room.capacity,
                    shortName=short_name,
                    roomTypeClassId=room.room_type_id.class_id,
                    ubicationId=room.ubication_id,
                    extraBedsAllowed=room.extra_beds_allowed,
                    roomAmenityIds=room.room_amenity_ids.ids
                    if room.room_amenity_ids
                    else None,
                    roomAmenityInName=room.room_amenity_ids.filtered(
                        lambda x: x.is_add_code_room_name
                    ).default_code
                    if room.room_amenity_ids.filtered(
                        lambda x: x.is_add_code_room_name
                    ).name
                    else "",
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
        room = self.env["pms.room"].sudo().browse(room_id)
        if not room.exists():
            raise MissingError(_("Room not found"))
        pms_api_check_access(user=self.env.user, records=room)
        PmsRoomInfo = self.env.datamodels["pms.room.info"]
        return PmsRoomInfo(
            id=room.id,
            name=room.name,
            roomTypeId=room.room_type_id,
            capacity=room.capacity,
            shortName=room.short_name,
            extraBedsAllowed=room.extra_beds_allowed,
        )

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
        room = self.env["pms.room"].sudo().browse(room_id)
        if not room.exists():
            raise MissingError(_("Room not found"))
        pms_api_check_access(user=self.env.user, records=room)
        room_vals = {}
        if pms_room_info_data.name:
            room_vals["name"] = pms_room_info_data.name
        if room_vals:
            room.write(room_vals)

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
        room = self.env["pms.room"].sudo().browse(room_id)
        if not room.exists():
            raise MissingError(_("Room not found"))
        pms_api_check_access(user=self.env.user, records=room)
        room.active = False

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
        pms_property = (
            self.env["pms.property"].sudo().browse(pms_room_info_param.pmsPropertyId)
        )
        if not pms_property.exists():
            raise MissingError(_("Property not found"))
        pms_api_check_access(user=self.env.user, records=pms_property)
        room = (
            self.env["pms.room"]
            .sudo()
            .create(
                {
                    "name": pms_room_info_param.name,
                    "room_type_id": pms_room_info_param.roomTypeId,
                    "capacity": pms_room_info_param.capacity,
                    "short_name": pms_room_info_param.shortName,
                    "pms_property_id": pms_room_info_param.pmsPropertyId,
                }
            )
        )
        return room.id
