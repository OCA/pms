# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from datetime import datetime, timedelta
from openerp import models, fields, api, _
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
_logger = logging.getLogger(__name__)


class HotelReservation(models.Model):
    _inherit = "hotel.reservation"

    @api.model
    def _generate_reservation_notif(self, action, ntype, title,
                                    product_id, reserv_id, partner_name,
                                    adults, children, checkin, checkout,
                                    folio_id, color, color_text, splitted,
                                    parent_reservation, room_name,
                                    partner_phone, state, fix_days):
        vals = super(HotelReservation, self)._generate_reservation_notif(
            action, ntype, title, product_id,
            reserv_id, partner_name, adults,
            children, checkin, checkout,
            folio_id, color, color_text, splitted, parent_reservation,
            room_name, partner_phone, state, fix_days)
        reserv = self.env['hotel.reservation'].browse(vals['reserv_id'])
        vals['reservation'].update({
            'fix_days': (reserv.wrid and reserv.wrid != '') or fix_days,
            'wchannel': (reserv.wchannel_id and reserv.wchannel_id.name),
        })
        return vals

    @api.multi
    def _hcalendar_reservation_data(self, reservations):
        vals = super(HotelReservation, self)._hcalendar_reservation_data(
                                                                reservations)
        hotel_reservation_obj = self.env['hotel.reservation']
        json_reservations = []
        for v_rval in vals[0]:
            reserv = hotel_reservation_obj.browse(v_rval[1])
            json_reservations.append((
                reserv.product_id.id,
                reserv.id,
                reserv.folio_id.partner_id.name,
                reserv.adults,
                reserv.children,
                reserv.checkin,
                reserv.checkout,
                reserv.folio_id.id,
                reserv.reserve_color,
                reserv.reserve_color_text,
                reserv.splitted,
                reserv.parent_reservation.id,
                # Read-Only
                False,
                # Fix Days
                (reserv.wrid and reserv.wrid != '') or reserv.splitted,
                # Fix Rooms
                False,
                reserv.overbooking))
            # Update tooltips
            vals[1][reserv.id].append(reserv.wchannel_id.name)
        return (json_reservations, vals[1])

    @api.multi
    def send_bus_notification(self, naction, ntype, ntitle=''):
        hotel_cal_obj = self.env['bus.hotel.calendar']
        for record in self:
            hotel_cal_obj.send_reservation_notification({
                'action': naction,
                'type': ntype,
                'title': ntitle,
                'product_id': record.product_id.id,
                'reserv_id': record.id,
                'partner_name': record.partner_id.name,
                'adults': record.adults,
                'children': record.children,
                'checkin': record.checkin,
                'checkout': record.checkout,
                'folio_id': record.folio_id.id,
                'reserve_color': record.reserve_color,
                'reserve_color_text': record.reserve_color_text,
                'splitted': record.splitted,
                'parent_reservation': record.parent_reservation and
                record.parent_reservation.id or 0,
                'room_name': record.product_id.name,
                'partner_phone': record.partner_id.mobile
                or record.partner_id.phone or _('Undefined'),
                'state': record.state,
                'fix_days': record.splitted or record.is_from_ota,
                'overbooking': record.overbooking,
                'price': record.folio_id.amount_total,
                'wrid': record.wrid,
            })

    @api.multi
    def confirm(self):
        for record in self:
            if record.to_assign == True:
                record.write({'to_read': False, 'to_assign': False})
        return super(HotelReservation, self).confirm()
