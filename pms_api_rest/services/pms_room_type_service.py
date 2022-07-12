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
        input_param=Datamodel("pms.room.type.search.param"),
        output_param=Datamodel("pms.room.type.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_room_types(self, room_type_search_param):
        room_type_all_properties = self.env["pms.room.type"].search(
            [("pms_property_ids", "=", False)]
        )
        if room_type_search_param.pmsPropertyIds:
            room_types = set()
            for index, prop in enumerate(room_type_search_param.pmsPropertyIds):
                room_types_with_query_property = self.env["pms.room.type"].search(
                    [("pms_property_ids", "=", prop)]
                )
                if index == 0:
                    room_types = set(room_types_with_query_property.ids)
                else:
                    room_types = room_types.intersection(
                        set(room_types_with_query_property.ids)
                    )
            room_types_total = list(
                set(list(room_types) + room_type_all_properties.ids)
            )
        else:
            room_types_total = list(room_type_all_properties.ids)
        domain = [
            ("id", "in", room_types_total),
        ]

        result_rooms = []
        PmsRoomTypeInfo = self.env.datamodels["pms.room.type.info"]
        for room in self.env["pms.room.type"].search(
            domain,
        ):

            result_rooms.append(
                PmsRoomTypeInfo(
                    id=room.id,
                    name=room.name,
                    pmsPropertyIds=room.pms_property_ids.mapped("id"),
                    defaultCode=room.default_code,
                    price=round(room.list_price,2),
                )
            )
        return result_rooms
