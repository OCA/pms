from odoo import _
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsBoardServiceService(Component):
    _inherit = "base.rest.service"
    _name = "pms.board.service.line.service"
    _usage = "board-service-lines"
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
        input_param=Datamodel("pms.board.service.line.search.param"),
        output_param=Datamodel("pms.board.service.line.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_board_service_lines(self, board_service_lines_search_param):
        domain = []
        if board_service_lines_search_param.boardServiceId:
            domain.append(
                (
                    "pms_board_service_room_type_id",
                    "=",
                    board_service_lines_search_param.boardServiceId,
                )
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

    @restapi.method(
        [
            (
                [
                    "/<int:board_service_line_id>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.board.service.line.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_board_service_line(self, board_service_line_id):
        board_service_line = self.env["pms.board.service.room.type.line"].search(
            [("id", "=", board_service_line_id)]
        )
        if board_service_line:
            PmsBoardServiceInfo = self.env.datamodels["pms.board.service.line.info"]
            return PmsBoardServiceInfo(
                id=board_service_line.id,
                name=board_service_line.pms_board_service_room_type_id.display_name,
                boardServiceId=board_service_line.pms_board_service_room_type_id.id,
                productId=board_service_line.product_id.id,
                amount=board_service_line.amount,
            )
        else:
            raise MissingError(_("Board service line not found"))
