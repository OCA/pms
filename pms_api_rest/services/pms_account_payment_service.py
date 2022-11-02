from datetime import datetime

from odoo import _
from odoo.odoo import fields
from odoo.odoo.exceptions import ValidationError
from odoo.odoo.tools import get_lang
from odoo.osv import expression

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


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
        domain_fields = [("state", "=", "posted")]
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
        domain_filter = list()
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
            domain_fields.extend(
                [
                    "&",
                    ("date", ">=", date_from),
                    ("date", "<", date_to),
                ]
            )
        if pms_payments_search_param.paymentMethodId:
            domain_fields.append(
                ("journal_id", "=", pms_payments_search_param.paymentMethodId)
            )
        # TODO: payment tyope filter (partner_type, payment_type, is_transfer)
        if domain_filter:
            domain = expression.AND([domain_fields, domain_filter[0]])
        else:
            domain = domain_fields

        PmsPaymentResults = self.env.datamodels["pms.payment.results"]
        PmsPaymentInfo = self.env.datamodels["pms.payment.info"]

        total_payments = self.env["account.payment"].search_count(domain)
        group_payments = self.env["account.payment"].read_group(
            domain=domain, fields=["amount:sum"], groupby=["payment_type"]
        )
        amount_result = 0
        if group_payments:
            for item in group_payments:
                total_inbound = (
                    item["amount"] if item["payment_type"] == "inbound" else 0
                )
                total_outbound = (
                    item["amount"] if item["payment_type"] == "outbound" else 0
                )
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
                    journalId=payment.journal_id.id if payment.journal_id else None,
                    date=payment.date.strftime("%d/%m/%Y"),
                    partnerId=payment.partner_id.id if payment.partner_id else None,
                    partnerName=payment.partner_id.name if payment.partner_id else None,
                    paymentType=payment.payment_type,
                    partnerType=payment.partner_type,
                    isTransfer=payment.is_internal_transfer,
                    reference=payment.ref if payment.ref else None,
                    createUid=payment.create_uid if payment.create_uid else None,
                )
            )

        return PmsPaymentResults(
            payments=result_payments, total=amount_result, totalPayments=total_payments
        )

    @restapi.method(
        [
            (
                [
                    "/cash-register",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.cash.register.search.param", is_list=False),
        output_param=Datamodel("pms.cash.register.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_cash_register(self, cash_register_search_param):
        statement = (
            self.env["account.bank.statement"]
            .sudo()
            .search(
                [
                    ("journal_id", "=", cash_register_search_param.journalId),
                ],
                limit=1,
            )
        )

        CashRegister = self.env.datamodels["pms.cash.register.info"]
        if not statement:
            return CashRegister()
        isOpen = True if statement.state == "open" else False
        return CashRegister(
            state="open" if isOpen else "close",
            userId=statement.user_id.id,
            balance=statement.balance_start if isOpen else statement.balance_end_real,
            dateTime=statement.create_date.strftime("%d/%m/%Y")
            if isOpen
            else statement.date_done.strftime("%d/%m/%Y"),
        )

    @restapi.method(
        [
            (
                [
                    "/p/cash-register",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.cash.register.action", is_list=False),
        output_param=Datamodel("pms.cash.register.result", is_list=False),
        auth="jwt_api_pms",
    )
    def cash_register(self, cash_register_action):
        PmsCashRegisterResult = self.env.datamodels["pms.cash.register.result"]
        if cash_register_action.action == "open":
            dict_result = self._action_open_cash_session(
                pms_property_id=cash_register_action.pmsPropertyId,
                amount=cash_register_action.amount,
                journal_id=cash_register_action.journalId,
                force=cash_register_action.forceAction,
            )
        elif cash_register_action.action == "close":
            dict_result = self._action_close_cash_session(
                pms_property_id=cash_register_action.pmsPropertyId,
                amount=cash_register_action.amount,
                journal_id=cash_register_action.journalId,
                force=cash_register_action.forceAction,
            )
        else:
            raise ValidationError(
                _("No action cash register found (only allowed open/close actions")
            )
        return PmsCashRegisterResult(
            result=dict_result["result"],
            diff=dict_result["diff"],
        )

    def _action_open_cash_session(self, pms_property_id, amount, journal_id, force):
        statement = (
            self.env["account.bank.statement"]
            .sudo()
            .search(
                [
                    ("journal_id", "=", journal_id),
                ],
                limit=1,
            )
        )
        if round(statement.balance_end_real, 2) == round(amount, 2) or force:
            self.env["account.bank.statement"].sudo().create(
                {
                    "name": datetime.today().strftime(get_lang(self.env).date_format)
                    + " ("
                    + self.env.user.login
                    + ")",
                    "date": datetime.today(),
                    "balance_start": amount,
                    "journal_id": journal_id,
                    "pms_property_id": pms_property_id,
                }
            )
            diff = round(amount - statement.balance_end_real, 2)
            return {"result": True, "diff": diff}
        else:
            diff = round(amount - statement.balance_end_real, 2)
            return {"result": False, "diff": diff}

    def _action_close_cash_session(self, pms_property_id, amount, journal_id, force):
        statement = (
            self.env["account.bank.statement"]
            .sudo()
            .search(
                [
                    ("journal_id", "=", journal_id),
                    ("state", "=", "open"),
                    ("pms_property_id", "=", pms_property_id),
                ],
                limit=1,
            )
        )
        if round(statement.balance_end, 2) == round(amount, 2):
            statement.sudo().balance_end_real = amount
            statement.sudo().button_post()
            return {
                "result": True,
                "diff": 0,
            }
        elif force:
            # Not call to button post to avoid create profit/loss line
            # (_check_balance_end_real_same_as_computed)
            if not statement.name:
                statement.sudo()._set_next_sequence()
            statement.sudo().balance_end_real = amount
            statement.write({"state": "posted"})
            lines_of_moves_to_post = statement.line_ids.filtered(
                lambda line: line.move_id.state != "posted"
            )
            if lines_of_moves_to_post:
                lines_of_moves_to_post.move_id._post(soft=False)
            diff = round(amount - statement.balance_end, 2)
            return {
                "result": True,
                "diff": diff,
            }
        else:
            diff = round(amount - statement.balance_end, 2)
            return {
                "result": False,
                "diff": diff,
            }
