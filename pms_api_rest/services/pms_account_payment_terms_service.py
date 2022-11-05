from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsAccountPaymentTermService(Component):
    _inherit = "base.rest.service"
    _name = "pms.account.payment.term.service"
    _usage = "payment-terms"
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
        output_param=Datamodel("pms.account.transaction.term.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_account_payment_terms(self):

        PmsAccountPaymenttermInfo = self.env.datamodels[
            "pms.account.transaction.term.info"
        ]
        res = []
        for payment_term in self.env["account.payment.term"].search([]):
            res.append(
                PmsAccountPaymenttermInfo(
                    id=payment_term.id,
                    name=payment_term.name,
                )
            )
        return res
