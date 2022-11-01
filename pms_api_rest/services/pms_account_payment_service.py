from datetime import datetime
from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component
from odoo.odoo import fields
from odoo.osv import expression


class PmsAccountPaymentService(Component):
    _inherit = "base.rest.service"
    _name = "pms.account.payment.service"
    _usage = "payments"
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
        input_param=Datamodel("pms.payment.search.param", is_list=False),
        output_param=Datamodel("pms.payment.results", is_list=False),
        auth="jwt_api_pms",
    )
    def get_payments(self, pms_payments_search_param):
        result_payments = []
        domain_fields = [("state","=","posted")]
        available_journals = ()
        if pms_payments_search_param.pmsPropertyId:
            available_journals = self.env["account.journal"].search(
                [
                    "&",
                    ("pms_property_ids", "in", pms_payments_search_param.pmsPropertyId),
                    ("pms_property_ids", "!=", False),
                ]
            )
        domain_fields.append(("journal_id", "in", available_journals.ids))
        domain_filter=list()
        if pms_payments_search_param.filter:
            # TODO: filter by folio and invoice
            for search in pms_payments_search_param.filter.split(" "):
                subdomains = [
                    [("name", "ilike", search)],
                    # [("folio_id.name", "ilike", search)],
                    [("partner_id.display_name", "ilike", search)],
                ]
                domain_filter.append(expression.OR(subdomains))

        if pms_payments_search_param.dateStart and pms_payments_search_param.dateEnd:
            date_from = fields.Date.from_string(pms_payments_search_param.dateStart)
            date_to = fields.Date.from_string(pms_payments_search_param.dateEnd)
            domain_fields.extend([
                "&",
                ("date", ">=", date_from),
                ("date", "<", date_to),
            ])
        if pms_payments_search_param.paymentMethodId:
            domain_fields.append(("journal_id","=",pms_payments_search_param.paymentMethodId))
        # TODO: payment tyope filter (partner_type, payment_type, is_transfer)
        if domain_filter:
            domain = expression.AND([domain_fields, domain_filter[0]])
        else:
            domain = domain_fields

        PmsPaymentResults = self.env.datamodels["pms.payment.results"]
        PmsPaymentInfo = self.env.datamodels["pms.payment.info"]

        total_payments = self.env["account.payment"].search_count(domain)
        group_payments = self.env["account.payment"].read_group(
            domain=domain,
            fields=["amount:sum"],
            groupby=["payment_type"]
        )
        amount_result = 0
        if group_payments:
            for item in group_payments:
                total_inbound = item["amount"] if item["payment_type"] == "inbound" else 0
                total_outbound = item["amount"] if item["payment_type"] == "outbound" else 0
            amount_result = total_inbound - total_outbound
        for payment in self.env["account.payment"].search(
            domain,
            order=pms_payments_search_param.orderBy,
            limit=pms_payments_search_param.limit,
            offset=pms_payments_search_param.offset,
        ):
            result_payments.append(
                PmsPaymentInfo(
                    id=payment.id,
                    name=payment.name if payment.name else None,
                    amount=payment.amount,
                    journalId=payment.journal_id.id
                    if payment.journal_id
                    else None,
                    date=payment.date.strftime("%d/%m/%Y"),
                    partnerId = payment.partner_id.id
                    if payment.partner_id
                    else None,
                    partnerName = payment.partner_id.name
                    if payment.partner_id
                    else None,
                    paymentType=payment.payment_type,
                    partnerType=payment.partner_type,
                    isTransfer=payment.is_internal_transfer,
                    reference=payment.ref if payment.ref else None,
                    createUid=payment.create_uid if payment.create_uid else None,
                )
            )

        return PmsPaymentResults(payments=result_payments, total=amount_result, totalPayments=total_payments)
