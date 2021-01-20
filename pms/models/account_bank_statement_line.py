from odoo import api, fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    statement_folio_ids = fields.Many2many(
        "pms.folio", string="Folios", ondelete="cascade"
    )
    reservation_ids = fields.Many2many(
        "pms.reservation", string="Reservations", ondelete="cascade"
    )
    service_ids = fields.Many2many("pms.service", string="Services", ondelete="cascade")

    @api.model
    def _prepare_move_line_default_vals(self, counterpart_account_id=None):
        line_vals_list = super(
            AccountBankStatementLine, self
        )._prepare_move_line_default_vals(counterpart_account_id)
        if self.statement_folio_ids:
            for line in line_vals_list:
                line.update(
                    {
                        "folio_ids": [(6, 0, self.statement_folio_ids.ids)],
                        "reservation_ids": [(6, 0, self.reservation_ids.ids)],
                        "service_ids": [(6, 0, self.service_ids.ids)],
                    }
                )
        return line_vals_list
