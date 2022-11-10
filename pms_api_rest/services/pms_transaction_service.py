import logging
from datetime import datetime

import pytz

from odoo import _, fields
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools import get_lang

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class PmsTransactionService(Component):
    _inherit = "base.rest.service"
    _name = "pms.transaction.service"
    _usage = "transactions"
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
        input_param=Datamodel("pms.transaction.search.param", is_list=False),
        output_param=Datamodel("pms.transaction.results", is_list=False),
        auth="jwt_api_pms",
    )
    def get_transactions(self, pms_transactions_search_param):
        result_transactions = []
        domain_fields = [
            ("state", "=", "posted"),
        ]

        if pms_transactions_search_param.transactionMethodId:
            domain_fields.append(
                ("journal_id", "=", pms_transactions_search_param.transactionMethodId),
            )
        elif pms_transactions_search_param.pmsPropertyId:
            pms_property = self.env["pms.property"].browse(
                pms_transactions_search_param.pmsPropertyId
            )
            available_journals = pms_property._get_payment_methods(
                automatic_included=True
            )
            # REVIEW: avoid send to app generic company journals
            available_journals = available_journals.filtered(
                lambda j: j.pms_property_ids
            )
            domain_fields.append(("journal_id", "in", available_journals.ids))
        domain_filter = list()
        if pms_transactions_search_param.filter:
            # TODO: filter by folio and invoice
            for search in pms_transactions_search_param.filter.split(" "):
                subdomains = [
                    [("name", "ilike", search)],
                    [("ref", "ilike", search)],
                    [("partner_id.display_name", "ilike", search)],
                ]
                domain_filter.append(expression.OR(subdomains))

        if (
            pms_transactions_search_param.dateStart
            and pms_transactions_search_param.dateEnd
        ):
            date_from = fields.Date.from_string(pms_transactions_search_param.dateStart)
            date_to = fields.Date.from_string(pms_transactions_search_param.dateEnd)
            domain_fields.extend(
                [
                    ("date", ">=", date_from),
                    ("date", "<=", date_to),
                ]
            )

        if pms_transactions_search_param.transactionType:
            domain_fields.append(
                (
                    "pms_api_transaction_type",
                    "=",
                    pms_transactions_search_param.transactionType,
                )
            )

        if domain_filter:
            domain = expression.AND([domain_fields, domain_filter[0]])
        else:
            domain = domain_fields

        PmsTransactionResults = self.env.datamodels["pms.transaction.results"]
        PmsTransactiontInfo = self.env.datamodels["pms.transaction.info"]
        total_transactions = self.env["account.payment"].search_count(domain)
        group_transactions = self.env["account.payment"].read_group(
            domain=domain, fields=["amount:sum"], groupby=["payment_type"]
        )
        amount_result = 0
        if group_transactions:
            total_inbound = next(
                (
                    item["amount"]
                    for item in group_transactions
                    if item["payment_type"] == "inbound"
                ),
                0,
            )
            total_outbound = next(
                (
                    item["amount"]
                    for item in group_transactions
                    if item["payment_type"] == "outbound"
                ),
                0,
            )
            amount_result = total_inbound - total_outbound
        transactions = self.env["account.payment"].search(
            domain,
            order=pms_transactions_search_param.orderBy,
            limit=pms_transactions_search_param.limit,
            offset=pms_transactions_search_param.offset,
        )
        for transaction in transactions:
            # In internal transfer payments, the APP only show
            # the outbound payment, with the countrapart journal id
            # (destinationJournalId), the domain ensure avoid
            # get the input internal transfer payment
            destination_journal_id = False
            if transaction.is_internal_transfer:
                if (
                    transaction.payment_type == "inbound"
                    and transaction.pms_api_counterpart_payment_id.id
                    in transactions.ids
                ):
                    continue
                outbound_transaction = (
                    transaction
                    if transaction.payment_type == "outbound"
                    else transaction.pms_api_counterpart_payment_id
                )
                inbound_transaction = (
                    transaction
                    if transaction.payment_type == "inbound"
                    else transaction.pms_api_counterpart_payment_id
                )
                transaction = (
                    outbound_transaction
                    if outbound_transaction
                    else inbound_transaction
                )
                if inbound_transaction:
                    destination_journal_id = inbound_transaction.journal_id.id

            result_transactions.append(
                PmsTransactiontInfo(
                    id=transaction.id,
                    name=transaction.name if transaction.name else None,
                    amount=round(transaction.amount, 2),
                    journalId=transaction.journal_id.id
                    if transaction.journal_id
                    else None,
                    destinationJournalId=destination_journal_id or None,
                    date=datetime.combine(
                        transaction.date, datetime.min.time()
                    ).isoformat(),
                    partnerId=transaction.partner_id.id
                    if transaction.partner_id
                    else None,
                    partnerName=transaction.partner_id.name
                    if transaction.partner_id
                    else None,
                    reference=transaction.ref if transaction.ref else None,
                    createUid=transaction.create_uid
                    if transaction.create_uid
                    else None,
                    transactionType=transaction.pms_api_transaction_type or None,
                )
            )
        return PmsTransactionResults(
            transactions=result_transactions,
            total=round(amount_result, 2),
            totalTransactions=total_transactions,
        )

    @restapi.method(
        [
            (
                [
                    "/<int:transaction_id>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.transaction.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_transaction(self, transaction_id):
        PmsTransactiontInfo = self.env.datamodels["pms.transaction.info"]
        transaction = self.env["account.payment"].browse(transaction_id)
        destination_journal_id = False
        if transaction.is_internal_transfer:
            destination_journal_id = (
                transaction.pms_api_counterpart_payment_id.journal_id.id
            )
        return PmsTransactiontInfo(
            id=transaction.id,
            name=transaction.name if transaction.name else None,
            amount=transaction.amount,
            journalId=transaction.journal_id.id if transaction.journal_id else None,
            destinationJournalId=destination_journal_id or None,
            date=datetime.combine(transaction.date, datetime.min.time()).isoformat(),
            partnerId=transaction.partner_id.id if transaction.partner_id else None,
            partnerName=transaction.partner_id.name if transaction.partner_id else None,
            reference=transaction.ref if transaction.ref else None,
            createUid=transaction.create_uid.id if transaction.create_uid else None,
            transactionType=transaction.pms_api_transaction_type or None,
        )

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.transaction.info", is_list=False),
        auth="jwt_api_pms",
    )
    def create_transaction(self, pms_transaction_info):
        pay_date = fields.Date.from_string(pms_transaction_info.date)
        payment_type, partner_type = self._get_mapper_transaction_type(
            pms_transaction_info.transactionType
        )
        journal = self.env["account.journal"].browse(pms_transaction_info.journalId)
        is_internal_transfer = (
            pms_transaction_info.transactionType == "internal_transfer"
        )
        partner_id = (
            pms_transaction_info.partnerId
            if pms_transaction_info.transactionType != "internal_transfer"
            else journal.company_id.partner_id.id
        )
        vals = {
            "amount": pms_transaction_info.amount,
            "journal_id": pms_transaction_info.journalId,
            "date": pay_date,
            "partner_id": partner_id,
            "ref": pms_transaction_info.reference,
            "state": "draft",
            "payment_type": payment_type,
            "partner_type": partner_type,
            "is_internal_transfer": is_internal_transfer,
        }
        if is_internal_transfer:
            vals["partner_bank_id"] = (
                self.env["account.journal"]
                .browse(pms_transaction_info.destinationJournalId)
                .bank_account_id.id
            )
        pay = self.env["account.payment"].create(vals)
        pay.sudo().action_post()
        if is_internal_transfer:
            counterpart_vals = {
                "amount": pms_transaction_info.amount,
                "journal_id": pms_transaction_info.destinationJournalId,
                "date": pay_date,
                "partner_id": partner_id,
                "ref": pms_transaction_info.reference,
                "state": "draft",
                "payment_type": "inbound",
                "partner_type": partner_type,
                "is_internal_transfer": is_internal_transfer,
            }
            countrepart_pay = self.env["account.payment"].create(counterpart_vals)
            countrepart_pay.sudo().action_post()
            pay.pms_api_counterpart_payment_id = countrepart_pay.id
            countrepart_pay.pms_api_counterpart_payment_id = pay.id
        return pay.id

    @restapi.method(
        [
            (
                [
                    "/p/<int:transaction_id>",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.transaction.info", is_list=False),
        auth="jwt_api_pms",
    )
    def update_transaction(self, transaction_id):
        return transaction_id

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
        statement = self._get_last_cash_session(
            journal_id=cash_register_search_param.journalId,
        )
        CashRegister = self.env.datamodels["pms.cash.register.info"]
        if not statement:
            return CashRegister()
        isOpen = True if statement.state == "open" else False
        timezone = pytz.timezone(self.env.context.get("tz") or "UTC")
        create_date_utc = pytz.UTC.localize(statement.create_date)
        create_date = create_date_utc.astimezone(timezone)

        return CashRegister(
            state="open" if isOpen else "close",
            userId=statement.user_id.id,
            balance=statement.balance_start if isOpen else statement.balance_end_real,
            dateTime=create_date.isoformat()
            if isOpen
            else statement.date_done.isoformat()
            if statement.date_done
            else None,
        )

    @restapi.method(
        [
            (
                [
                    "/cash-register",
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
        statement = self._get_last_cash_session(
            journal_id=journal_id,
            pms_property_id=pms_property_id,
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
        statement = self._get_last_cash_session(
            journal_id=journal_id,
            pms_property_id=pms_property_id,
        )
        session_payments = (
            self.env["account.payment"]
            .sudo()
            .search(
                [
                    ("journal_id", "=", journal_id),
                    ("pms_property_id", "=", pms_property_id),
                    ("state", "=", "posted"),
                    ("create_date", ">=", statement.create_date),
                ]
            )
        )
        session_payments_amount = sum(
            session_payments.filtered(lambda x: x.payment_type == "inbound").mapped(
                "amount"
            )
        ) - sum(
            session_payments.filtered(lambda x: x.payment_type == "outbound").mapped(
                "amount"
            )
        )

        compute_end_balance = round(
            statement.balance_start + session_payments_amount, 2
        )
        if round(compute_end_balance, 2) == round(amount, 2):
            self._session_create_statement_lines(
                session_payments, statement, amount, auto_conciliation=True
            )
            if statement.all_lines_reconciled:
                statement.sudo().button_validate_or_action()
            return {
                "result": True,
                "diff": 0,
            }
        elif force:
            self._session_create_statement_lines(
                session_payments, statement, amount, auto_conciliation=False
            )
            diff = round(amount - compute_end_balance, 2)
            return {
                "result": True,
                "diff": diff,
            }
        else:
            diff = round(amount - compute_end_balance, 2)
            return {
                "result": False,
                "diff": diff,
            }

    @restapi.method(
        [
            (
                [
                    "/transactions-report",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.report.search.param", is_list=False),
        output_param=Datamodel("pms.report", is_list=False),
        auth="jwt_api_pms",
    )
    def transactions_report(self, pms_transaction_report_search_param):
        pms_property_id = pms_transaction_report_search_param.pmsPropertyId
        date_from = fields.Date.from_string(
            pms_transaction_report_search_param.dateFrom
        )
        date_to = fields.Date.from_string(pms_transaction_report_search_param.dateTo)

        report_wizard = self.env["cash.daily.report.wizard"].create(
            {
                "date_start": date_from,
                "date_end": date_to,
                "pms_property_id": pms_property_id,
            }
        )
        result = report_wizard._export()
        file_name = result["xls_filename"]
        base64EncodedStr = result["xls_binary"]
        PmsResponse = self.env.datamodels["pms.report"]
        return PmsResponse(fileName=file_name, binary=base64EncodedStr)

    def _get_mapper_transaction_type(self, transaction_type):
        if transaction_type == "internal_transfer":
            # counterpart is inbound supplier
            return "outbound", "supplier"
        elif transaction_type == "customer_inbound":
            return "inbound", "customer"
        elif transaction_type == "customer_outbound":
            return "outbound", "customer"
        elif transaction_type == "supplier_inbound":
            return "inbound", "supplier"
        elif transaction_type == "supplier_outbound":
            return "outbound", "supplier"

    def _session_create_statement_lines(
        self, session_payments, statement, amount, auto_conciliation
    ):
        payment_statement_line_match_dict = []
        for record in session_payments:
            journal = record.journal_id
            vals = {
                "date": record.date,
                "journal_id": journal.id,
                "amount": record.amount
                if record.payment_type == "inbound"
                else -record.amount,
                "payment_ref": record.ref,
                "partner_id": record.partner_id.id,
                "pms_property_id": record.pms_property_id.id,
                "statement_id": statement.id,
            }
            statement_line = self.env["account.bank.statement.line"].sudo().create(vals)
            payment_statement_line_match_dict.append(
                {
                    "payment_id": record.id,
                    "statement_line_id": statement_line.id,
                }
            )

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

        if auto_conciliation:
            for match in payment_statement_line_match_dict:
                payment = self.env["account.payment"].sudo().browse(match["payment_id"])
                statement_line = (
                    self.env["account.bank.statement.line"]
                    .sudo()
                    .browse(match["statement_line_id"])
                )
                payment_move_line = payment.move_id.line_ids.filtered(
                    lambda x: x.reconciled is False
                    and x.journal_id == journal
                    and (
                        x.account_id == journal.payment_debit_account_id
                        or x.account_id == journal.payment_credit_account_id
                    )
                )
                statement_line_move = statement_line.move_id
                statement_move_line = statement_line_move.line_ids.filtered(
                    lambda line: line.account_id.reconcile
                    or line.account_id == line.journal_id.suspense_account_id
                )
                if payment_move_line and statement_move_line:
                    statement_move_line.account_id = payment_move_line.account_id
                    lines_to_reconcile = payment_move_line + statement_move_line
                    lines_to_reconcile.reconcile()

    def _get_last_cash_session(self, journal_id, pms_property_id=False):
        domain = [("journal_id", "=", journal_id)]
        if pms_property_id:
            domain.append(("pms_property_id", "=", pms_property_id))
        return (
            self.env["account.bank.statement"]
            .sudo()
            .search(
                domain,
                order="date desc, id desc",
                limit=1,
            )
        )
