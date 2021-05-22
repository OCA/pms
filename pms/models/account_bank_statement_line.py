from odoo import api, fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    folio_ids = fields.Many2many(
        string="Folios",
        comodel_name="pms.folio",
        ondelete="cascade",
        relation="account_bank_statement_folio_rel",
        column1="account_journal_id",
        column2="folio_id",
    )
    reservation_ids = fields.Many2many(
        string="Reservations",
        help="Reservations in which the Account Bank Statement Lines are included",
        comodel_name="pms.reservation",
        ondelete="cascade",
        relation="account_bank_statement_reservation_rel",
        column1="account_bank_statement_id",
        column2="reservation_id",
    )
    service_ids = fields.Many2many(
        string="Services",
        help="Services in which the Account Bank Statement Lines are included",
        comodel_name="pms.service",
        ondelete="cascade",
        relation="account_bank_statement_service_rel",
        column1="account_bank_statement_id",
        column2="service_id",
    )

    @api.model
    def _prepare_move_line_default_vals(self, counterpart_account_id=None):
        line_vals_list = super(
            AccountBankStatementLine, self
        )._prepare_move_line_default_vals(counterpart_account_id)
        if self.folio_ids:
            for line in line_vals_list:
                line.update(
                    {
                        "folio_ids": [(6, 0, self.folio_ids.ids)],
                    }
                )
        return line_vals_list
