from odoo import _
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsBoardServiceService(Component):
    _inherit = "base.rest.service"
    _name = "pms.board.service.service"
    _usage = "board-service"
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
        input_param=Datamodel("pms.board.service.search.param"),
        output_param=Datamodel("pms.board.service.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_board_services(self, board_services_search_param):
        domain = []
        if board_services_search_param.name:
            domain.append(("name", "like", board_services_search_param.name))
        if board_services_search_param.roomTypeId:
            domain.append(
                ("pms_room_type_id", "=", board_services_search_param.roomTypeId)
            )
        if board_services_search_param.pmsPropertyId:
            domain.extend(
                [
                    "|",
                    (
                        "pms_property_ids",
                        "in",
                        board_services_search_param.pmsPropertyId,
                    ),
                    ("pms_property_ids", "=", False),
                ]
            )

        result_board_services = []
        PmsBoardServiceInfo = self.env.datamodels["pms.board.service.info"]
        for board_service in self.env["pms.board.service.room.type"].search(
            domain,
        ):
            result_board_services.append(
                PmsBoardServiceInfo(
                    id=board_service.id,
                    name=board_service.pms_board_service_id.display_name,
                    roomTypeId=board_service.pms_room_type_id.id,
                    amount=board_service.amount,
                )
            )
        return result_board_services

    @restapi.method(
        [
            (
                [
                    "/<int:board_service_id>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.board.service.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_board_service(self, board_service_id):
        board_service = self.env["pms.board.service.room.type"].search(
            [("id", "=", board_service_id)]
        )
        if board_service:
            PmsBoardServiceInfo = self.env.datamodels["pms.board.service.info"]
            return PmsBoardServiceInfo(
                id=board_service.id,
                name=board_service.pms_board_service_id.display_name,
                roomTypeId=board_service.pms_room_type_id.id,
                amount=board_service.amount,
            )
        else:
            raise MissingError(_("Board Service not found"))

    @restapi.method(
        [
            (
                [
                    "/<int:board_service_id>/lines",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.search.param"),
        output_param=Datamodel("pms.board.service.line.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_board_service_lines(self, board_service_id, pms_search_param):
        domain = list()
        domain.append(("pms_board_service_room_type_id", "=", board_service_id))
        if pms_search_param.pmsPropertyId:
            domain.extend(
                [
                    "|",
                    (
                        "pms_property_ids",
                        "in",
                        pms_search_param.pmsPropertyId,
                    ),
                    ("pms_property_ids", "=", False),
                ]
            )
        result_board_service_lines = []
        PmsBoardServiceInfo = self.env.datamodels["pms.board.service.line.info"]
        for line in self.env["pms.board.service.room.type.line"].search(
            domain,
        ):
            result_board_service_lines.append(
                PmsBoardServiceInfo(
                    id=line.id,
                    name=line.pms_board_service_room_type_id.display_name,
                    boardServiceId=line.pms_board_service_room_type_id.id,
                    productId=line.product_id.id,
                    amount=line.amount,
                )
            )
        return result_board_service_lines
