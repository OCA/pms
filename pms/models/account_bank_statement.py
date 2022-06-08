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
            payment_move_line = line._get_payment_move_lines_to_reconcile()
            statement_move_line = line.move_id.line_ids.filtered(
                lambda line: line.account_id.reconcile
                or line.account_id == line.journal_id.suspense_account_id
            )
            if payment_move_line and statement_move_line:
                statement_move_line.account_id = payment_move_line.account_id
                lines_to_reconcile = payment_move_line + statement_move_line
                lines_to_reconcile.reconcile()
