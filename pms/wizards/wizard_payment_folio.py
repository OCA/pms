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
    journal_id = fields.Many2one(
        string="Journal",
        required=True,
        comodel_name="account.journal",
        domain="[('id', 'in', available_journal_ids)]",
    )
    available_journal_ids = fields.Many2many(
        comodel_name="account.journal",
        compute="_compute_available_journal_ids",
    )
    payment_method_line_id = fields.Many2one(
        string="Payment Method",
        required=True,
        comodel_name="account.payment.method.line",
        domain="[('id', 'in', available_payment_method_line_ids)]",
    )
    available_payment_method_line_ids = fields.Many2many(
        comodel_name="account.payment.method.line",
        compute="_compute_available_payment_method_line_ids",
    )
    amount = fields.Float(digits=("Product Price"))
    date = fields.Date(required=True, default=fields.Date.context_today)
    partner_id = fields.Many2one(string="Partner", comodel_name="res.partner")

    def _get_allowed_method_lines(self):
        self.ensure_one()
        if not self.folio_id:
            return self.env["account.payment.method.line"]
        return self.folio_id.pms_property_id._get_payment_methods(
            room_ids=self.folio_id.mapped(
                "reservation_ids.reservation_line_ids.room_id.id"
            ),
        )

    @api.depends("folio_id")
    def _compute_available_journal_ids(self):
        for wizard in self:
            method_lines = wizard._get_allowed_method_lines()
            wizard.available_journal_ids = method_lines.mapped("journal_id")

    @api.depends("journal_id")
    def _compute_available_payment_method_line_ids(self):
        for wizard in self:
            method_lines = wizard._get_allowed_method_lines()
            journal = wizard.journal_id
            wizard.available_payment_method_line_ids = method_lines.filtered(
                lambda line, j=journal: line.journal_id == j
            )

    @api.onchange("journal_id")
    def _onchange_journal_id(self):
        if self.available_payment_method_line_ids:
            self.payment_method_line_id = self.available_payment_method_line_ids[0]
        else:
            self.payment_method_line_id = False

    def button_payment(self):
        self.env["pms.folio"].do_payment(
            self.payment_method_line_id,
            self.env.user,
            self.amount,
            self.folio_id,
            reservations=False,
            services=False,
            partner=self.partner_id,
            date=self.date,
        )
