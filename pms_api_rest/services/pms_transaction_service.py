from datetime import datetime

from odoo import _, fields
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools import get_lang

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


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
        # In internal transfer payments, the APP only show
        # the output payment, with the countrapart journal id
        # (destinationJournalId), the domain ensure avoid
        # get the input internal transfer payment
        domain_fields = [
            ("state", "=", "posted"),
            "|",
            ("is_internal_transfer", "=", False),
            ("payment_type", "=", "outbound"),
        ]

        available_journals = ()
        if pms_transactions_search_param.pmsPropertyId:
            available_journals = self.env["account.journal"].search(
                [
                    (
                        "pms_property_ids",
                        "in",
                        pms_transactions_search_param.pmsPropertyId,
                    ),
                ]
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
                    "&",
                    ("date", ">=", date_from),
                    ("date", "<", date_to),
                ]
            )
        if pms_transactions_search_param.transactionMethodId:
            domain_fields.append(
                ("journal_id", "=", pms_transactions_search_param.transactionMethodId)
            )

        if pms_transactions_search_param.transactionType:
            domain_fields.append(
                "pms_api_transaction_type",
                "=",
                pms_transactions_search_param.transactionType,
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
        for transaction in self.env["account.payment"].search(
            domain,
            order=pms_transactions_search_param.orderBy,
            limit=pms_transactions_search_param.limit,
            offset=pms_transactions_search_param.offset,
        ):
            destination_journal_id = False
            if transaction.is_internal_transfer:
                destination_journal_id = transaction.internal_transfer_id.journal_id.id
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
            destination_journal_id = transaction.internal_transfer_id.journal_id.id
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
        # TODO: FIX fron send data format ('%Y-%m-%d')
        # use fields.Date.from_string(pms_transaction_info.date)
        pay_date_wrong_format = pms_transaction_info.date
        pay_date = datetime.strptime(pay_date_wrong_format, "%m/%d/%Y")
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
            pay.internal_transfer_id = countrepart_pay.id
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
            dateTime=statement.create_date.isoformat()
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
        date_from = (
            datetime.strptime(pms_transaction_report_search_param.dateFrom, "%Y-%m-%d"),
        )
        date_to = (
            datetime.strptime(pms_transaction_report_search_param.dateTo, "%Y-%m-%d"),
        )
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
