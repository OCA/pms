from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


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
            result_properties.append(
                PmsPropertyInfo(
                    id=prop.id,
                    name=prop.name,
                    company=prop.company_id.name,
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
                    simpleOutColor=prop.simple_out_color,
                    simpleInColor=prop.simple_in_color,
                    simpleFutureColor=prop.simple_future_color,
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
            )

        return res

    @restapi.method(
        [
            (
                [
                    "/<int:property_id>/paymentmethods",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.account.journal.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_method_payments_property(self, property_id):

        pms_property = self.env["pms.property"].search([("id", "=", property_id)])
        PmsAccountJournalInfo = self.env.datamodels["pms.account.journal.info"]
        res = []
        if not pms_property:
            pass
        else:
            for method in pms_property._get_payment_methods(automatic_included=True):
                payment_method = self.env["account.journal"].search(
                    [("id", "=", method.id)]
                )
                res.append(
                    PmsAccountJournalInfo(
                        id=payment_method.id,
                        name=payment_method.name,
                        allowed_pms_payments=payment_method.allowed_pms_payments,
                    )
                )
        return res
