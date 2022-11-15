from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsRoomTypeClassService(Component):
    _inherit = "base.rest.service"
    _name = "pms.room.type.class.service"
    _usage = "room-type-classes"
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
        if room_type_class_search_param.pmsPropertyIds:
            room_type_classes = (
                self.env["pms.room"]
                .search(
                    [
                        (
                            "pms_property_id",
                            "in",
                            room_type_class_search_param.pmsPropertyIds,
                        )
                    ]
                )
                .mapped("room_type_id")
                .mapped("class_id")
            )
        else:
            room_type_classes = self.env["pms.room.type.class"].search(
                [("pms_property_ids", "=", False)]
            )
        result_room_type_class = []
        PmsRoomTypeClassInfo = self.env.datamodels["pms.room.type.class.info"]
        for room in room_type_classes:
            result_room_type_class.append(
                PmsRoomTypeClassInfo(
                    id=room.id,
                    name=room.name,
                    pmsPropertyIds=room.pms_property_ids.mapped("id"),
                )
            )
        return result_room_type_class
