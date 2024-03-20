# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _set_transaction_cancel(self):
        allowed_states = ("draft", "authorized")
        target_state = "cancel"
        tx_to_process, _, _ = self._filter_transaction_state(
            allowed_states, target_state
        )
        folios = tx_to_process.mapped("folio_ids")
        folios.action_cancel()
        return super()._set_transaction_cancel()
