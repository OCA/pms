# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _compute_reservations_count(self):
        hotel_reservation_obj = self.env['hotel.reservation']
        for record in self:
            record.reservations_count = hotel_reservation_obj.search_count([
                ('partner_id.id', '=', record.id)
            ])

    def _compute_folios_count(self):
        hotel_folio_obj = self.env['hotel.folio']
        for record in self:
            record.folios_count = hotel_folio_obj.search_count([
                ('partner_id.id', '=', record.id)
            ])

    reservations_count = fields.Integer('Reservations', compute='_compute_reservations_count')
    folios_count = fields.Integer('Folios', compute='_compute_folios_count')
