# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import except_orm
from odoo import models, fields, api, _

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def rm_add_payment(self, code, payment):
        reservation = self.env['hotel.reservation'].search([
            '|', ('localizator', '=', code),
            ('folio_id.name', '=', code)])
        if not reservation:
            return False
        if reservation:
            for cashpay in payment['CashPayments']:
                vals = {
                    'journal_id': 7,  # TODO:config setting
                    'partner_id': reservation.partner_invoice_id.id,
                    'amount': cashpay['Amount'],
                    'payment_date': cashpay['DateTime'],
                    'communication': reservation.name,
                    'folio_id': reservation.folio_id.id,
                    'payment_type': 'inbound',
                    'payment_method_id': 1,
                    'partner_type': 'customer',
                    'state': 'draft',
                }
                pay = self.create(vals)
            for cashpay in payment['CreditCardPayments']:
                vals = {
                    'journal_id': 15,  # TODO:config setting
                    'partner_id': reservation.partner_invoice_id.id,
                    'amount': cashpay['Amount'],
                    'payment_date': cashpay['DateTime'],
                    'communication': reservation.name,
                    'folio_id': reservation.folio_id.id,
                    'payment_type': 'inbound',
                    'payment_method_id': 1,
                    'partner_type': 'customer',
                    'state': 'draft',
                }
                pay = self.create(vals)
        pay.post()
        return True
