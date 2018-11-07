# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import except_orm
from odoo import models, fields, api, _

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    folio_id = fields.Many2one('hotel.folio', string='Folio')
    amount_total_folio = fields.Float(
        compute="_compute_folio_amount", store=True,
        string="Total amount in folio",
    )

    """WIP"""
    @api.multi
    def return_payment_folio(self):
        journal = self.journal_id
        partner = self.partner_id
        amount = self.amount
        reference = self.communication
        account_move_lines = self.move_line_ids.filtered(lambda x: (
            x.account_id.internal_type == 'receivable'))
        return_line_vals = {
            'move_line_ids': [(6, False, [x.id for x in account_move_lines])],
            'partner_id': partner.id,
            'amount': amount,
            'reference': reference,
            }
        return_vals = {
            'journal_id': journal.id,
            'line_ids': [(0, 0, return_line_vals)],
            }
        return_pay = self.env['payment.return'].create(return_vals)
        return {
            'name': 'Folio Payment Return',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'payment.return',
            'type': 'ir.actions.act_window',
            'res_id': return_pay.id,
        }
    @api.multi
    def modify(self):
        self.cancel()
        vals = {
            'journal_id': self.journal_id,
            'partner_id': self.partner_id,
            'amount': self.amount,
            'payment_date': self.payment_date,
            'communication': self.communication,
            'folio_id': self.folio_id}
        self.update(vals)
        self.post()

    @api.multi
    def delete(self):
        self.cancel()
        self.move_name = ''
        self.unlink()

    @api.multi
    @api.depends('state')
    def _compute_folio_amount(self):
        # FIXME: Finalize method
        res = []
        fol = ()
        for payment in self:
            amount_pending = 0
            total_amount = 0
            if payment.folio_id:
                fol = payment.env['hotel.folio'].search([
                    ('id', '=', payment.folio_id.id)
                ])
            else:
                return
            if not any(fol):
                return
            if len(fol) > 1:
                raise except_orm(_('Warning'), _('This pay is related with \
                                                more than one Reservation.'))
            else:
                fol.compute_amount()
            return res
