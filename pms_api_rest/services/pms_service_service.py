import logging
from datetime import datetime

from odoo import _
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class PmsServiceService(Component):
    _inherit = "base.rest.service"
    _name = "pms.service.service"
    _usage = "services"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/<int:service_id>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.service.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_service(self, service_id):
        service = self.env["pms.service"].search([("id", "=", service_id)])
        if not service:
            raise MissingError(_("Service not found"))
        PmsServiceInfo = self.env.datamodels["pms.service.info"]
        lines = [
            self.env.datamodels["pms.service.line.info"](
                id=line.id,
                date=datetime.combine(line.date, datetime.min.time()).isoformat(),
                priceUnit=line.price_unit,
                discount=line.discount,
                quantity=line.day_qty,
            )
            for line in service.service_line_ids
        ]
        return PmsServiceInfo(
            id=service.id,
            name=service.name,
            productId=service.product_id.id,
            quantity=service.product_qty,
            priceTotal=round(service.price_total, 2),
            priceSubtotal=round(service.price_subtotal, 2),
            priceTaxes=round(service.price_tax, 2),
            discount=round(service.discount, 2),
            isBoardService=service.is_board_service,
            serviceLines=lines,
        )

    @restapi.method(
        [
            (
                [
                    "/<int:service_id>",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.service.info", is_list=False),
        auth="jwt_api_pms",
    )
    def update_service(self, service_id, service_data):
        service = self.env["pms.service"].search([("id", "=", service_id)])
        if not service:
            raise MissingError(_("Service not found"))
        vals = {}
        if service_data.serviceLines:
            cmds_lines = []
            date_list = []
            for line_data in service_data.serviceLines:
                date_line = datetime.strptime(line_data.date, "%Y-%m-%d").date()
                date_list.append(date_line)
                service_line = service.service_line_ids.filtered(
                    lambda l: l.date == date_line
                )
                # 1- update values in existing lines
                if service_line:
                    line_vals = self._get_service_lines_mapped(line_data, service_line)
                    cmds_lines.append((1, service_line.id, line_vals))
                # 2- create new lines
                else:
                    line_vals = self._get_service_lines_mapped(line_data)
                    line_vals["date"] = line_data.date
                    cmds_lines.append((0, False, line_vals))
            # 3- delete old lines:
            for line in service.service_line_ids.filtered(
                lambda l: l.date not in date_list
            ):
                cmds_lines.append((2, line.id))
            if cmds_lines:
                vals["service_line_ids"] = cmds_lines
        _logger.info(vals)
        if vals:
            service.write(vals)

    def _get_service_lines_mapped(self, origin_data, service_line=False):
        # Return dict witch reservation.lines values (only modified if line exist,
        # or all pass values if line not exist)
        line_vals = {}
        if origin_data.priceUnit and (
            not service_line or origin_data.priceUnit != service_line.price_unit
        ):
            line_vals["price_unit"] = origin_data.priceUnit
        if origin_data.discount and (
            not service_line or origin_data.discount != service_line.discount
        ):
            line_vals["discount"] = origin_data.discount
        if origin_data.quantity and (
            not service_line or origin_data.quantity != service_line.day_qty
        ):
            line_vals["day_qty"] = origin_data.quantity
        return line_vals

    @restapi.method(
        [
            (
                [
                    "/<int:service_id>",
                ],
                "DELETE",
            )
        ],
        auth="jwt_api_pms",
    )
    def delete_service(self, service_id):
        # esto tb podría ser con un browse
        service = self.env["pms.service"].search([("id", "=", service_id)])
        if service:
            service.unlink()
        else:
            raise MissingError(_("Service not found"))

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
                    date=datetime.combine(
                        service_line.date, datetime.min.time()
                    ).isoformat(),
                    priceUnit=round(service_line.price_unit, 2),
                    discount=round(service_line.discount, 2),
                    quantity=service_line.day_qty,
                )
            )
        return result_service_lines
