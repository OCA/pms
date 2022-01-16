from odoo import fields, models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    pms_property_id = fields.Many2one(
        string="Property",
        help="Properties with access to the element",
        copy=False,
        comodel_name="pms.property",
    )
    company_id = fields.Many2one(
        string="Company",
        help="The company for Account Bank Statement",
    )

    def button_post(self):
        """
        Override the default method to add autoreconcile payments and statement lines
        """
        lines_of_moves_to_post = self.line_ids.filtered(
            lambda line: line.move_id.state != "posted"
        )
        super(AccountBankStatement, self).button_post()
        for line in lines_of_moves_to_post:
            folio_ids = line.folio_ids.ids
            if folio_ids:
                to_reconcile_ids = self.env["account.move.line"].search(
                    [
                        ("move_id.folio_ids", "in", folio_ids),
                        ("reconciled", "=", False),
                        "|",
                        (
                            "account_id",
                            "=",
                            self.journal_id.payment_debit_account_id.id,
                        ),
                        (
                            "account_id",
                            "=",
                            self.journal_id.payment_credit_account_id.id,
                        ),
                        ("journal_id", "=", self.journal_id.id),
                    ]
                )
                if to_reconcile_ids:
                    statement_move_line = line.move_id.line_ids.filtered(
                        lambda line: line.account_id.reconcile
                    )
                    payment_line = self.env["account.move.line"].browse(
                        to_reconcile_ids.ids
                    )[0]
                    if payment_line and statement_move_line:
                        statement_move_line.account_id = payment_line.account_id
                        lines_to_reconcile = payment_line + statement_move_line
                        lines_to_reconcile.reconcile()
