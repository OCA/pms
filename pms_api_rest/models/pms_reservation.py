import json

from odoo import fields, models


class PmsReservation(models.Model):
    _inherit = "pms.reservation"

    pwa_action_buttons = fields.Char(compute="_compute_pwa_action_buttons")

    def _compute_pwa_action_buttons(self):
        """Return ordered button list, where the first button is
        the preditive action, the next are active actions:
        - "Assign":     Predictive: Reservation by assign
                        Active- Idem
        - "checkin":    Predictive- state 'confirm' and checkin day
                        Active- Idem and assign
        - "checkout":   Predictive- Pay, onboard and checkout day
                        Active- Onboard and checkout day
        - "Paymen":     Predictive- Onboard and pending amount > 0
                        Active- pending amount > 0
        - "Invoice":    Predictive- qty invoice > 0, onboard, pending amount = 0
                        Active- qty invoice > 0
        - "Cancel":     Predictive- Never
                        Active- state in draft, confirm, onboard, full onboard
        """
        for reservation in self:
            active_buttons = {}
            for k in ["Assign", "Checkin", "Checkout", "Payment", "Invoice", "Cancel"]:
                if k == "Assign":
                    if reservation.to_assign:
                        active_buttons[k] = True
                    else:
                        active_buttons[k] = False
                elif k == "Checkin":
                    if reservation.allowed_checkin:
                        active_buttons[k] = True
                    else:
                        active_buttons[k] = False
                elif k == "Checkout":
                    if reservation.allowed_checkout:
                        active_buttons[k] = True
                    else:
                        active_buttons[k] = False
                elif k == "Payment":
                    if reservation.folio_pending_amount > 0:
                        active_buttons[k] = True
                    else:
                        active_buttons[k] = False
                elif k == "Invoice":
                    if reservation.invoice_status == "to invoice":
                        active_buttons[k] = True
                    else:
                        active_buttons[k] = False
                elif k == "Cancel":
                    if reservation.allowed_cancel:
                        active_buttons[k] = True
                    else:
                        active_buttons[k] = False

            reservation.pwa_action_buttons = json.dumps(active_buttons)
