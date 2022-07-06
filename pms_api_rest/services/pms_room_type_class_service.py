from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsRoomTypeClassService(Component):
    _inherit = "base.rest.service"
    _name = "pms.room.type.class.service"
    _usage = "room-type-class"
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
        input_param=Datamodel("pms.room.type.class.search.param"),
        output_param=Datamodel("pms.room.type.class.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_room_type_class(self, room_type_class_search_param):
        room_type_class_all_properties = self.env["pms.room.type.class"].search(
            [("pms_property_ids", "=", False)]
        )
        if room_type_class_search_param.pmsPropertyIds:
            room_type_class = set()
            for index, prop in enumerate(room_type_class_search_param.pmsPropertyds):
                room_type_class_with_query_property = self.env[
                    "pms.room.type.class"
                ].search([("pms_property_ids", "=", prop)])
                if index == 0:
                    room_type_class = set(room_type_class_with_query_property.ids)
                else:
                    room_type_class = room_type_class.intersection(
                        set(room_type_class_with_query_property.ids)
                    )
            room_type_class_total = list(
                set(list(room_type_class) + room_type_class_all_properties.ids)
            )
        else:
            room_type_class_total = list(room_type_class_all_properties.ids)
        domain = [
            ("id", "in", room_type_class_total),
        ]

        result_room_type_class = []
        PmsRoomTypeClassInfo = self.env.datamodels["pms.room.type.class.info"]
        for room in self.env["pms.room.type.class"].search(
            domain,
        ):

            result_room_type_class.append(
                PmsRoomTypeClassInfo(
                    id=room.id,
                    name=room.name,
                    pmsPropertyIds=room.pms_property_ids.mapped("id"),
                )
            )
        return result_room_type_class
