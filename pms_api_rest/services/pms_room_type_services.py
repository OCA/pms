from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsRoomTypeService(Component):
    _inherit = "base.rest.service"
    _name = "pms.room.type.service"
    _usage = "room-types"
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
    def get_room_types(self, room_type_search_param):
        domain = []
        if room_type_search_param.name:
            domain.append(("name", "like", room_type_search_param.name))
        if room_type_search_param.id:
            domain.append(("id", "=", room_type_search_param.id))
        result_rooms = []
        PmsRoomTypeInfo = self.env.datamodels["pms.room.type.info"]
        for room in (
            self.env["pms.room.type"]
            .sudo()
            .search(
                domain,
            )
        ):

            result_rooms.append(
                PmsRoomTypeInfo(
                    id=room.id,
                    name=room.name,
                )
            )
        return result_rooms
