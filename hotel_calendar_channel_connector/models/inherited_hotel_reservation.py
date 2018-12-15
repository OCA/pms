# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from odoo import models, api
_logger = logging.getLogger(__name__)


class HotelReservation(models.Model):
    _inherit = "hotel.reservation"

    @api.multi
    def _hcalendar_reservation_data(self, reservations):
        vals = super(HotelReservation, self)._hcalendar_reservation_data(reservations)
        hotel_reservation_obj = self.env['hotel.reservation']
        for v_rval in vals[0]:
            reserv = hotel_reservation_obj.browse(v_rval['id'])
            v_rval.update({
                'fix_days': reserv.splitted or reserv.is_from_ota,
            })
            # Update tooltips
            vals[1][reserv.id].update({
                'ota_name': reserv.channel_bind_ids[0].ota_id.name if any(reserv.channel_bind_ids) else False
            })
        return vals

    @api.multi
    def generate_bus_values(self, naction, ntype, ntitle=''):
        vals = super(HotelReservation, self).generate_bus_values(naction, ntype, ntitle)
        vals.update({
            'fix_days': self.splitted or self.is_from_ota,
        })
        return vals

    @api.multi
    def confirm(self):
        for record in self:
            if record.to_assign:
                record.write({'to_read': False, 'to_assign': False})
        return super(HotelReservation, self).confirm()
