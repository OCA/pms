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
        domain = []
        if account_journal_search_param.pmsPropertyId:
            domain.extend(
                [
                    "|",
                    (
                        "pms_property_ids",
                        "in",
                        account_journal_search_param.pmsPropertyId,
                    ),
                    ("pms_property_ids", "=", False),
                ]
            )
        PmsAccountJournalInfo = self.env.datamodels["pms.account.journal.info"]
        result_account_journals = []
        for account_journal in self.env["account.journal"].search(
            domain,
        ):
            result_account_journals.append(
                PmsAccountJournalInfo(
                    id=account_journal.id,
                    name=account_journal.name,
                    allowedPayments=account_journal.allowed_pms_payments,
                )
            )
        return result_account_journals
