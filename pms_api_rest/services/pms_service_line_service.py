from datetime import datetime

from odoo import _
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsServiceLineService(Component):
    _inherit = "base.rest.service"
    _name = "pms.service.line.service"
    _usage = "service-lines"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/<int:service_line_id>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.service.line.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_service_line(self, service_line_id):
        service_line = self.env["pms.service.line"].search(
            [("id", "=", service_line_id)]
        )
        if not service_line:
            raise MissingError(_("Service line not found"))
        PmsServiceLineInfo = self.env.datamodels["pms.service.line.info"]

        return PmsServiceLineInfo(
            id=service_line.id,
            date=datetime.combine(service_line.date, datetime.min.time()).isoformat(),
            priceUnit=round(service_line.price_unit, 2),
            discount=round(service_line.discount, 2),
            quantity=service_line.day_qty,
        )

    @restapi.method(
        [
            (
                [
                    "/p/<int:service_line_id>",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.service.line.info"),
        auth="jwt_api_pms",
    )
    def update_service_line(self, service_line_id, pms_service_line_info_data):
        service_line = self.env["pms.service.line"].search(
            [("id", "=", service_line_id)]
        )
        vals = {}
        if service_line:
            if pms_service_line_info_data.date:
                vals["date"] = datetime.strptime(
                    pms_service_line_info_data.date, "%Y-%m-%d"
                ).date()
            if pms_service_line_info_data.discount:
                vals["discount"] = pms_service_line_info_data.discount
            if pms_service_line_info_data.quantity:
                vals["day_qty"] = pms_service_line_info_data.quantity
            if pms_service_line_info_data.priceUnit:
                vals["price_unit"] = pms_service_line_info_data.priceUnit
            service_line.write(vals)
        else:
            raise MissingError(_("Service line not found"))

    @restapi.method(
        [
            (
                [
                    "/<int:service_line_id>",
                ],
                "DELETE",
            )
        ],
        auth="jwt_api_pms",
    )
    def delete_service_line(self, service_line_id):
        # esto tb podría ser con un browse
        service_line = self.env["pms.service.line"].search(
            [("id", "=", service_line_id)]
        )
        if service_line:
            service_line.unlink()
        else:
            raise MissingError(_("Service line not found"))
