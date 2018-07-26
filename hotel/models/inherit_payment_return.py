# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2018-Darío Lodeiros Vázquez
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
# ---------------------------------------------------------------------------
from openerp import models, fields, api, _


class PaymentReturn(models.Model):

    _inherit = 'payment.return'

    folio_id = fields.Many2one('hotel.folio', string='Folio')

    @api.multi
    def action_confirm(self):
        pay = super(PaymentReturn,self).action_confirm()
        if pay:
            folio_ids = []
            for line in self.line_ids:
               payments = self.env['account.payment'].search([('move_line_ids','in',line.move_line_ids.ids)])
               folio_ids += payments.mapped('folio_id.id')
            folios = self.env['hotel.folio'].browse(folio_ids)
            folios.compute_invoices_amount()
