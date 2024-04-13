import base64

from odoo import fields

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

from ..pms_api_rest_utils import url_image_pms_api_rest


class PmsPropertyService(Component):
    _inherit = "base.rest.service"
    _name = "pms.property.service"
    _usage = "properties"
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
        output_param=Datamodel("pms.property.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_properties(self):
        domain = [("user_ids", "in", [self.env.user.id])]
        result_properties = []
        PmsPropertyInfo = self.env.datamodels["pms.property.info"]
        for prop in self.env["pms.property"].search(
            domain,
        ):
            state_name = False
            if prop.state_id:
                state_name = (
                    self.env["res.country.state"]
                    .search([("id", "=", prop.state_id.id)])
                    .name
                )
            result_properties.append(
                PmsPropertyInfo(
                    id=prop.id,
                    name=prop.name,
                    stateName=state_name if state_name else None,
                    defaultPricelistId=prop.default_pricelist_id.id,
                    colorOptionConfig=prop.color_option_config,
                    preReservationColor=prop.pre_reservation_color,
                    confirmedReservationColor=prop.confirmed_reservation_color,
                    paidReservationColor=prop.paid_reservation_color,
                    onBoardReservationColor=prop.on_board_reservation_color,
                    paidCheckinReservationColor=prop.paid_checkin_reservation_color,
                    outReservationColor=prop.out_reservation_color,
                    staffReservationColor=prop.staff_reservation_color,
                    toAssignReservationColor=prop.to_assign_reservation_color,
                    pendingPaymentReservationColor=prop.pending_payment_reservation_color,
                    overPaymentColor=prop.overpayment_reservation_color,
                    simpleOutColor=prop.simple_out_color,
                    simpleInColor=prop.simple_in_color,
                    simpleFutureColor=prop.simple_future_color,
                    language=prop.lang,
                    hotelImageUrl=url_image_pms_api_rest(
                        "pms.property", prop.id, "hotel_image_pms_api_rest"
                    ),
                )
            )
        return result_properties

    @restapi.method(
        [
            (
                [
                    "/<int:property_id>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.property.info"),
        auth="jwt_api_pms",
    )
    def get_property(self, property_id):
        pms_property = self.env["pms.property"].search([("id", "=", property_id)])
        res = []
        PmsPropertyInfo = self.env.datamodels["pms.property.info"]
        if not pms_property:
            pass
        else:
            res = PmsPropertyInfo(
                id=pms_property.id,
                name=pms_property.name,
                company=pms_property.company_id.name,
                defaultPricelistId=pms_property.default_pricelist_id.id,
                colorOptionConfig=pms_property.color_option_config,
                preReservationColor=pms_property.pre_reservation_color,
                confirmedReservationColor=pms_property.confirmed_reservation_color,
                paidReservationColor=pms_property.paid_reservation_color,
                onBoardReservationColor=pms_property.on_board_reservation_color,
                paidCheckinReservationColor=pms_property.paid_checkin_reservation_color,
                outReservationColor=pms_property.out_reservation_color,
                staffReservationColor=pms_property.staff_reservation_color,
                toAssignReservationColor=pms_property.to_assign_reservation_color,
                pendingPaymentReservationColor=pms_property.pending_payment_reservation_color,
                language=pms_property.lang,
            )

        return res

    @restapi.method(
        [
            (
                [
                    "/<int:property_id>/users",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("res.users.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_users(self, pms_property_id):
        result_users = []
        ResUsersInfo = self.env.datamodels["res.users.info"]
        users = self.env["res.users"].search(
            [("pms_property_ids", "in", pms_property_id)]
        )
        for user in users:
            result_users.append(
                ResUsersInfo(
                    id=user.id,
                    name=user.name,
                    # TODO: Disabled by performance issues
                    #  userImageBase64=user.partner_id.image_1024 or None,
                    userImageBase64=None,
                )
            )
        return result_users

    @restapi.method(
        [
            (
                [
                    "/traveller-report",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.report.search.param", is_list=False),
        output_param=Datamodel("pms.report", is_list=False),
        auth="jwt_api_pms",
    )
    def transactions_report(self, pms_report_search_param):
        pms_property_id = pms_report_search_param.pmsPropertyId
        pms_property = self.env["pms.property"].search([("id", "=", pms_property_id)])
        date_from = fields.Date.from_string(pms_report_search_param.dateFrom)
        report_wizard = self.env["traveller.report.wizard"].create(
            {
                "date_target": date_from,
                "pms_property_id": pms_property_id,
            }
        )
        content = report_wizard.generate_checkin_list(
            pms_property_id=pms_property_id,
            date_target=date_from,
        )
        file_name = pms_property.institution_property_id + ".999"
        base64EncodedStr = base64.b64encode(str.encode(content))
        PmsResponse = self.env.datamodels["pms.report"]
        return PmsResponse(fileName=file_name, binary=base64EncodedStr)
