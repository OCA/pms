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
        if room_search_param.id:
            domain.append(("id", "=", room_search_param.id))
        if room_search_param.pms_property_id:
            domain.append(("pms_property_id", "=", room_search_param.pms_property_id))

        result_rooms = []
        PmsRoomInfo = self.env.datamodels["pms.room.info"]
        for room in self.env["pms.room"].search(
            domain,
        ).sorted("capacity"):

            result_rooms.append(
                PmsRoomInfo(
                    id=room.id,
                    name=room.name,
                    roomTypeId=room.room_type_id,
                    capacity=room.capacity,
                )
            )
        return result_rooms
