from datetime import datetime

from odoo import _
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsServiceService(Component):
    _inherit = "base.rest.service"
    _name = "pms.reservation.line.service"
    _usage = "services"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/<int:service_id>/service-lines",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.service.line.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_service_lines(self, service_id):
        service = self.env["pms.service"].search([("id", "=", service_id)])
        if not service:
            raise MissingError(_("Service not found"))
        result_service_lines = []
        PmsServiceLineInfo = self.env.datamodels["pms.service.line.info"]
        for service_line in service.service_line_ids:
            result_service_lines.append(
                PmsServiceLineInfo(
                    id=service_line.id,
                    isBoardService=service_line.is_board_service,
                    productId=service_line.product_id.id,
                    date=datetime.combine(
                        service_line.date, datetime.min.time()
                    ).isoformat(),
                    priceUnit=round(service_line.price_unit,2),
                    priceTotal=round(service_line.price_day_total,2),
                    discount=round(service_line.discount,2),
                )
            )
        return result_service_lines
