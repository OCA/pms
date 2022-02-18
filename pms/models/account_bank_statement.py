from odoo import api, fields, models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"
    _check_pms_properties_auto = True

    pms_property_id = fields.Many2one(
        string="Property",
        help="Properties with access to the element",
        comodel_name="pms.property",
        readonly=False,
        compute="_compute_pms_property_id",
        store=True,
        copy=False,
        check_pms_properties=True,
    )
    journal_id = fields.Many2one(check_pms_properties=True)

    @api.depends("journal_id")
    def _compute_pms_property_id(self):
        for record in self:
            if len(record.journal_id.pms_property_ids) == 1:
                record.pms_property_id = record.journal_id.pms_property_ids[0]
            elif not record.pms_property_id:
                record.pms_property_id = False

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
                    payment_lines = self.env["account.move.line"].browse(
                        to_reconcile_ids.ids
                    )
                    # We try to reconcile by amount
                    payment_line = False
                    for record in payment_lines:
                        payment_line = (
                            record if abs(record.balance) == line.amount else False
                        )
                    if payment_line and statement_move_line:
                        statement_move_line.account_id = payment_line.account_id
                        lines_to_reconcile = payment_line + statement_move_line
                        lines_to_reconcile.reconcile()
