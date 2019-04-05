# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def create(self, vals):
        if self.env.context.get('invoice_origin', False):
            vals.update({'origin': self.env.context.get['invoice_origin']})
        return super(AccountInvoice, self).create(vals)

    """WIP"""
    @api.multi
    def action_folio_payments(self):
        self.ensure_one()
        sales = self.mapped('invoice_line_ids.sale_line_ids.order_id')
        folios = self.env['hotel.folio'].search([('order_id.id','in',sales.ids)])
        payments_obj = self.env['account.payment']
        payments = payments_obj.search([('folio_id','in',folios.ids)])
        payment_ids = payments.mapped('id')
        return{
            'name': _('Payments'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.payment',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', payment_ids)],
        }

    from_folio = fields.Boolean(compute='_computed_folio_origin')
    folio_ids = fields.Many2many(
            comodel_name='hotel.folio', compute='_computed_folio_origin')

    @api.multi
    def action_invoice_open(self):
        to_open_invoices_without_vat = self.filtered(lambda inv: inv.state != 'open' and inv.partner_id.vat == False)
        if to_open_invoices_without_vat:
            vat_error = _("We need the VAT of the following companies")
            for invoice in to_open_invoices_without_vat:
                vat_error += ", " + invoice.partner_id.name
            raise ValidationError(vat_error)
        return super(AccountInvoice, self).action_invoice_open()

    @api.multi
    def _computed_folio_origin(self):
        for inv in self:
            folios = inv.mapped('invoice_line_ids.reservation_ids.folio_id')
            folios |= inv.mapped('invoice_line_ids.service_ids.folio_id')
            if folios:
                inv.from_folio = True
                inv.folio_ids = [(6, 0, folios.ids)]
