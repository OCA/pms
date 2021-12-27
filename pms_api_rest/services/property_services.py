from datetime import datetime

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsPropertyComponent(Component):
    _inherit = "base.rest.service"
    _name = "pms.property.service"
    _usage = "properties"
    _collection = "pms.reservation.service"

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.property.search.param"),
        output_param=Datamodel("pms.property.info", is_list=True),
        auth="public",
    )
    def get_properties(self,property_search_param):
        domain = []
        if property_search_param.name:
            domain.append(("name", "like", property_search_param.name))
        if property_search_param.id:
            domain.append(("id", "=", property_search_param.id))
        result_properties = []
        PmsPropertyInfo = self.env.datamodels["pms.property.info"]
        for prop in (
            self.env["pms.property"]
            .sudo()
            .search(
                domain,
            )
        ):
            result_properties.append(
                PmsPropertyInfo(
                    id=prop.id,
                    name=prop.name,
                    company=prop.company_id.name,
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
        auth="public",
    )
    def get_property(self, property_id):
        pms_property = (
            self.env["pms.property"].sudo().search([("id", "=", property_id)])
        )
        res = []
        PmsPropertyInfo = self.env.datamodels["pms.property.info"]
        if not pms_property:
            pass
        else:
            res = PmsPropertyInfo(
                id=pms_property.id,
                name=pms_property.name,
                company=pms_property.company_id.name,
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
        output_param=Datamodel("pms.account.journal.info",is_list=True),
        auth="public",
    )
    def get_method_payments_property(self, property_id):

        property = (
            self.env["pms.property"].sudo().search([("id", "=", property_id)])
        )
        PmsAccountJournalInfo = self.env.datamodels["pms.account.journal.info"]
        res = []
        if not property:
            pass
        else:
            for method in  property._get_payment_methods(
                automatic_included=True
            ):
                payment_method = (
                    self.env["account.journal"].sudo().search([("id", "=", method.id)])
                )
                res.append(
                    PmsAccountJournalInfo(
                        id=payment_method.id,
                        name=payment_method.name,
                        allowed_pms_payments=payment_method.allowed_pms_payments,
                    )
                )
        return res