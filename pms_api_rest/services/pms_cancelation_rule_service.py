from odoo import _
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

from ..pms_api_rest_utils import pms_api_check_access


class PmsCancelationRuleService(Component):
    _inherit = "base.rest.service"
    _name = "pms.cancelation.rule.service"
    _usage = "cancelation-rules"
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
        input_param=Datamodel("pms.cancelation.rule.search.param"),
        output_param=Datamodel("pms.cancelation.rule.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_cancelation_rules(self, cancelation_rule_search_param):
        domain = []
        if cancelation_rule_search_param.pricelistId:
            domain.append(
                ("pricelist_ids", "in", [cancelation_rule_search_param.pricelistId])
            )
        if cancelation_rule_search_param.pmsPropertyId:
            domain.extend(
                [
                    "|",
                    (
                        "pms_property_ids",
                        "in",
                        [cancelation_rule_search_param.pmsPropertyId],
                    ),
                    ("pms_property_ids", "=", False),
                ]
            )
        result_cancelation_rules = []
        PmsCancelationRuleInfo = self.env.datamodels["pms.cancelation.rule.info"]
        cancelation_rules = self.env["pms.cancelation.rule"].sudo().search(domain)
        pms_api_check_access(user=self.env.user, records=cancelation_rules)
        for cancelation_rule in cancelation_rules:
            result_cancelation_rules.append(
                PmsCancelationRuleInfo(
                    id=cancelation_rule.id,
                    name=cancelation_rule.name,
                )
            )
        return result_cancelation_rules

    @restapi.method(
        [
            (
                [
                    "/<int:cancelation_rule_id>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.cancelation.rule.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_cancelation_rule(self, cancelation_rule_id):
        cancelation_rule = self.env["pms.cancelation.rule"].sudo.search(
            [("id", "=", cancelation_rule_id)]
        )
        if cancelation_rule:
            pms_api_check_access(user=self.env.user, records=cancelation_rule)
            PmsCancelationRuleInfo = self.env.datamodels["pms.cancelation.rule.info"]
            return PmsCancelationRuleInfo(
                id=cancelation_rule.id,
                name=cancelation_rule.name,
            )
        else:
            raise MissingError(_("Cancelation Rule not found"))
