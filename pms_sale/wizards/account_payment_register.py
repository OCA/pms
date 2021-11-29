# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _create_payments(self):
        payment = super()._create_payments()
        reservations = payment.reconciled_invoice_ids.line_ids.mapped(
            "pms_reservation_id"
        )
        for reservation in reservations:
            reservation.action_confirm()
        return payment
