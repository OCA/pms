from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsAccountJournalService(Component):
    _inherit = "base.rest.service"
    _name = "pms.account.journal.service"
    _usage = "account-journals"
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
        input_param=Datamodel("pms.account.journal.search.param"),
        output_param=Datamodel("pms.account.journal.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_method_payments(self, account_journal_search_param):
        pms_property = self.env["pms.property"].search(
            [("id", "=", account_journal_search_param.pmsPropertyId)]
        )
        PmsAccountJournalInfo = self.env.datamodels["pms.account.journal.info"]
        result_account_journals = []
        if not pms_property:
            pass
        else:
            for payment_method in pms_property._get_payment_methods(automatic_included=True):
                # REVIEW: avoid send to app generic company journals
                if not payment_method.pms_property_ids:
                    continue
                result_account_journals.append(
                    PmsAccountJournalInfo(
                        id=payment_method.id,
                        name=payment_method.name,
                        type=payment_method.type,
                        allowedPayments=payment_method.allowed_pms_payments,
                    )
                )

        return result_account_journals
