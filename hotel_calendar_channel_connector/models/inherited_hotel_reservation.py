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
        # TODO: Improve performance by doing a SQL as in get_hcalendar_reservations_data()
        hotel_reservation_obj = self.env['hotel.reservation']
        for v_rval in vals[0]:
            reserv = hotel_reservation_obj.browse(v_rval['id'])
            v_rval.update({
                'fix_days': reserv.splitted or reserv.is_from_ota,
            })
            # Update tooltips
            if any(reserv.channel_bind_ids):
                vals[1][reserv.id].update({
                    'ota_name': reserv.channel_bind_ids[0].ota_id.name,
                    'ota_reservation_id': reserv.channel_bind_ids[0].ota_reservation_id,
                    'external_id': reserv.channel_bind_ids[0].external_id,
                })
            elif reserv.splitted and reserv.parent_reservation.channel_bind_ids:
                # chunks in splitted reservation has not channel_bind_ids
                vals[1][reserv.id].update({
                    'ota_name': reserv.parent_reservation.channel_bind_ids[0].ota_id.name,
                    'ota_reservation_id': reserv.parent_reservation.channel_bind_ids[0].ota_reservation_id,
                    'external_id': reserv.parent_reservation.channel_bind_ids[0].external_id,
                })
            # REVIEW: What happens if the reservation is splitted and no parent with channel_bind_ids ¿?
        return vals

    @api.multi
    def generate_bus_values(self, naction, ntype, ntitle=''):
        self.ensure_one()
        vals = super(HotelReservation, self).generate_bus_values(naction, ntype, ntitle)
        vals.update({
            'fix_days': self.splitted or self.is_from_ota,
        })
        if any(self.channel_bind_ids):
            vals.update({
                'ota_name': self.channel_bind_ids[0].ota_id.name,
                'ota_reservation_id': self.channel_bind_ids[0].ota_reservation_id,
                'external_id': self.channel_bind_ids[0].external_id,
            })
        return vals

    @api.multi
    def confirm(self):
        for record in self:
            if record.to_assign:
                record.write({'to_assign': False})
        return super(HotelReservation, self).confirm()
