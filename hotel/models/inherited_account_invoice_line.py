# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import api, fields, models, _

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    reservation_ids = fields.Many2many(
        'hotel.reservation',
        'reservation_invoice_rel',
        'invoice_line_id', 'reservation_id',
        string='Reservations', readonly=True, copy=False)
    service_ids = fields.Many2many(
        'hotel.service',
        'service_line_invoice_rel',
        'invoice_line_id', 'service_id',
        string='Services', readonly=True, copy=False)
    reservation_line_ids = fields.Many2many(
        'hotel.reservation.line',
        'reservation_line_invoice_rel',
        'invoice_line_id', 'reservation_line_id',
        string='Reservation Lines', readonly=True, copy=False)
