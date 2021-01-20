import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class WizardPaymentFolio(models.TransientModel):

    _name = "wizard.payment.folio"
    _description = "Payments"

    @api.model
    def default_folio_id(self):
        return self.env["pms.folio"].browse(self._context.get("active_id", [])).id

    @api.model
    def _default_amount(self):
        folio = self.env["pms.folio"].browse(self._context.get("active_id", []))
        return folio.pending_amount

    @api.model
    def _default_partner(self):
        folio = self.env["pms.folio"].browse(self._context.get("active_id", []))
        return folio.partner_id.id

    folio_id = fields.Many2one(
        "pms.folio",
        string="Folio",
        required=True,
        default=default_folio_id,
    )
    reservation_ids = fields.Many2many(
        "pms.reservation",
        string="Reservations",
    )
    service_ids = fields.Many2many(
        "pms.service",
        string="Services",
    )
    payment_method_id = fields.Many2one(
        "account.journal",
        string="Payment Method",
        required=True,
        domain="[('id', 'in', allowed_method_ids)]",
    )
    allowed_method_ids = fields.Many2many(
        "account.journal",
        "allowed_payment_journal_rel",
        "payment_id",
        "journal_id",
        compute="_compute_allowed_method_ids",
        store="True",
    )
    amount = fields.Float("Amount", digits=("Product Price"), default=_default_amount)
    date = fields.Date("Date", default=fields.Date.context_today, required=True)
    partner_id = fields.Many2one("res.partner", default=_default_partner)

    @api.depends("folio_id")
    def _compute_allowed_method_ids(self):
        self.ensure_one()
        journal_ids = False
        if self.folio_id:
            journal_ids = self.folio_id.pms_property_id._get_payment_methods().ids
        self.allowed_method_ids = journal_ids

    def button_payment(self):
        BankStatementLine = self.env["account.bank.statement.line"]
        line = self._get_statement_line_vals(
            journal=self.payment_method_id,
            receivable_account=self.payment_method_id.suspense_account_id,
            user=self.env.user,
            amount=self.amount,
            folios=self.folio_id,
            partner=self.partner_id,
            date=self.date,
        )
        BankStatementLine.sudo().create(line)

    def _get_statement_line_vals(
        self,
        journal,
        receivable_account,
        user,
        amount,
        folios,
        reservations=False,
        services=False,
        partner=False,
        date=False,
    ):
        property_folio_id = folios.mapped("pms_property_id.id")
        if len(property_folio_id) != 1:
            raise ValidationError(_("Only can payment by property"))
        statement = (
            self.env["account.bank.statement"]
            .sudo()
            .search(
                [
                    ("journal_id", "=", journal.id),
                    ("property_id", "=", property_folio_id[0]),
                    ("state", "=", "open"),
                ]
            )
        )
        reservation_ids = reservations.ids if reservations else []
        service_ids = services.ids if services else []
        # TODO: If not open statement, create new, with cash control option
        if statement:
            return {
                "date": date,
                "amount": amount,
                "partner_id": partner.id if partner else False,
                "statement_folio_ids": [(6, 0, folios.ids)],
                "reservation_ids": [(6, 0, reservation_ids)],
                "service_ids": [(6, 0, service_ids)],
                "payment_ref": folios.mapped("name"),
                "statement_id": statement.id,
                "journal_id": statement.journal_id.id,
                "counterpart_account_id": receivable_account.id,
            }
        else:
            return False
