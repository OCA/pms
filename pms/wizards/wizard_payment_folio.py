import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class WizardPaymentFolio(models.TransientModel):

    _name = "wizard.payment.folio"
    _description = "Payments"

    folio_id = fields.Many2one(
        "pms.folio",
        string="Folio",
        required=True,
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
    amount = fields.Float("Amount", digits=("Product Price"))
    date = fields.Date("Date", default=fields.Date.context_today, required=True)
    partner_id = fields.Many2one("res.partner")

    @api.depends("folio_id")
    def _compute_allowed_method_ids(self):
        self.ensure_one()
        journal_ids = False
        if self.folio_id:
            journal_ids = self.folio_id.pms_property_id._get_payment_methods().ids
        self.allowed_method_ids = journal_ids

    def button_payment(self):
        self.env["pms.folio"].do_payment(
            self.payment_method_id,
            self.payment_method_id.suspense_account_id,
            self.env.user,
            self.amount,
            self.folio_id,
            reservations=False,
            services=False,
            partner=self.partner_id,
            date=self.date,
        )
