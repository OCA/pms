import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class WizardPaymentFolio(models.TransientModel):

    _name = "wizard.payment.folio"
    _description = "Payments"

    folio_id = fields.Many2one(
        string="Folio",
        required=True,
        comodel_name="pms.folio",
    )
    reservation_ids = fields.Many2many(
        string="Reservations",
        comodel_name="pms.reservation",
    )
    service_ids = fields.Many2many(
        string="Services",
        comodel_name="pms.service",
    )
    payment_method_id = fields.Many2one(
        string="Payment Method",
        required=True,
        comodel_name="account.journal",
        domain="[('id', 'in', allowed_method_ids)]",
    )
    allowed_method_ids = fields.Many2many(
        store="True",
        comodel_name="account.journal",
        relation="allowed_payment_journal_rel",
        column1="payment_id",
        column2="journal_id",
        compute="_compute_allowed_method_ids",
    )
    amount = fields.Float(string="Amount", digits=("Product Price"))
    date = fields.Date(string="Date", required=True, default=fields.Date.context_today)
    partner_id = fields.Many2one(string="Partner", comodel_name="res.partner")

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
