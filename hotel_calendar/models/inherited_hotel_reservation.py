# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
_logger = logging.getLogger(__name__)


class HotelReservation(models.Model):
    _inherit = 'hotel.reservation'

    @api.model
    def _hcalendar_reservation_data(self, reservations):
        json_reservations = []
        json_reservation_tooltips = {}
        for reserv in reservations:
            json_reservations.append([
                reserv.room_id.id,
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
                reserv.parent_reservation and reserv.parent_reservation.id
                or False,
                False,  # Read-Only
                reserv.splitted,   # Fix Days
                False,  # Fix Rooms
                reserv.overbooking])
            num_split = 0
            if reserv.splitted:
                master_reserv = reserv.parent_reservation or reserv
                num_split = self.search_count([
                    ('folio_id', '=', reserv.folio_id.id),
                    '|', ('parent_reservation', '=', master_reserv.id),
                    ('id', '=', master_reserv.id),
                    ('splitted', '=', True),
                ])
            json_reservation_tooltips.update({
                reserv.id: [
                    reserv.folio_id.partner_id.name,
                    reserv.folio_id.partner_id.mobile or
                    reserv.folio_id.partner_id.phone or _('Undefined'),
                    reserv.checkin,
                    num_split,
                    reserv.folio_id.amount_total]
            })
        return (json_reservations, json_reservation_tooltips)

    @api.model
    def _hcalendar_room_data(self, rooms):
        pricelist_id = self.env['ir.default'].sudo().get(
            'res.config.settings', 'parity_pricelist_id')
        if pricelist_id:
            pricelist_id = int(pricelist_id)
        json_rooms = []
        for room in rooms:
            json_rooms.append((
                room.id,
                room.name,
                room.capacity,
                '', # Reserved for type code
                room.shared_room,
                room.room_type_id
                and ['pricelist', room.room_type_id.id, pricelist_id,
                     room.room_type_id.name]
                or 0,
                room.room_type_id.name,
                room.room_type_id.id,
                room.floor_id.id,
                room.room_amenities.ids))
        return json_rooms

    @api.model
    def _hcalendar_event_data(self, events):
        json_events = []
        for event in events:
            json_events.append([
                event.id,
                event.name,
                event.start,
                event.location,
            ])
        return json_events

    @api.model
    def get_hcalendar_reservations_data(self, dfrom, dto, rooms):
        date_start = fields.Date.from_string(dfrom) - timedelta(days=1)
        date_start_str = date_start.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        reservations_raw = self.env['hotel.reservation'].search(
            [
                ('room_id', 'in', rooms.ids),
                ('state', 'in',
                 ['draft', 'confirm', 'booking', 'done', False]),
            ],
            order="checkin DESC, checkout ASC, adults DESC, children DESC")
        reservations_ll = self.env['hotel.reservation'].search([
            ('checkin', '<=', dto),
            ('checkout', '>=', date_start_str)
        ])
        reservations_lr = self.env['hotel.reservation'].search([
            ('checkin', '>=', date_start_str),
            ('checkout', '<=', dto)
        ])
        reservations = (reservations_ll | reservations_lr) & reservations_raw
        return self._hcalendar_reservation_data(reservations)

    @api.model
    def get_hcalendar_pricelist_data(self, dfrom, dto):
        pricelist_id = self.env['ir.default'].sudo().get(
            'res.config.settings', 'parity_pricelist_id')
        if pricelist_id:
            pricelist_id = int(pricelist_id)
        date_start = fields.Date.from_string(dfrom) - timedelta(days=1)
        date_end = fields.Date.from_string(dto)
        date_diff = abs((date_end - date_start).days) + 1
        # Get Prices
        json_rooms_prices = {pricelist_id: []}
        room_typed_ids = self.env['hotel.room.type'].search(
            [],
            order='hcal_sequence ASC')
        room_pr_cached_obj = self.env['room.pricelist.cached']

        for room_type_id in room_typed_ids:
            days = {}
            for i in range(0, date_diff):
                ndate = date_start + timedelta(days=i)
                ndate_str = ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)
                prod_price_id = room_pr_cached_obj.search([
                    ('room_id', '=', room_type_id.id),
                    ('date', '=', ndate_str)
                ], limit=1)
                days.update({
                    ndate.strftime("%d/%m/%Y"): prod_price_id and
                                                prod_price_id.price or
                                                room_type_id.product_id.with_context(
                                                    quantity=1,
                                                    date=ndate_str,
                                                    pricelist=pricelist_id).price
                })
            json_rooms_prices[pricelist_id].append({
                'room': room_type_id.id,
                'days': days,
                'title': room_type_id.name,
            })
        return json_rooms_prices

    @api.model
    def get_hcalendar_restrictions_data(self, dfrom, dto):
        restriction_id = self.env['ir.default'].sudo().get(
            'res.config.settings', 'parity_restrictions_id')
        if restriction_id:
            restriction_id = int(restriction_id)
        date_start = fields.Date.from_string(dfrom) - timedelta(days=1)
        date_end = fields.Date.from_string(dto)
        date_diff = abs((date_end - date_start).days) + 1
        # Get Prices
        json_rooms_rests = {}
        room_types = self.env['hotel.room.type'].search(
            [],
            order='hcal_sequence ASC')
        room_type_rest_obj = self.env['hotel.room.type.restriction.item']
        for room_type in room_types:
            days = {}
            for i in range(0, date_diff):
                ndate = date_start + timedelta(days=i)
                ndate_str = ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)
                rest_id = room_type_rest_obj.search([
                    ('room_type_id', '=', room_type.id),
                    ('date', '>=', ndate_str),
                    ('applied_on', '=', '0_room_type'),
                    ('restriction_id', '=', restriction_id)
                ], limit=1)
                if rest_id and (rest_id.min_stay or rest_id.min_stay_arrival or
                                rest_id.max_stay or rest_id.max_stay_arrival or
                                rest_id.closed or rest_id.closed_arrival or
                                rest_id.closed_departure):
                    days.update({
                        ndate.strftime("%d/%m/%Y"): (
                            rest_id.min_stay,
                            rest_id.min_stay_arrival,
                            rest_id.max_stay,
                            rest_id.max_stay_arrival,
                            rest_id.closed,
                            rest_id.closed_arrival,
                            rest_id.closed_departure)
                    })
            json_rooms_rests.update({room_type.id: days})
        return json_rooms_rests

    @api.model
    def get_hcalendar_events_data(self, dfrom, dto):
        date_start = fields.Date.from_string(dfrom) - timedelta(days=1)
        date_start_str = date_start.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        user_id = self.env['res.users'].browse(self.env.uid)
        domain = []
        if user_id.pms_allowed_events_tags:
            domain.append(('categ_ids', 'in', user_id.pms_allowed_events_tags))
        if user_id.pms_denied_events_tags:
            domain.append(
                ('categ_ids', 'not in', user_id.pms_denied_events_tags))
        events_raw = self.env['calendar.event'].search(domain)
        events_ll = self.env['calendar.event'].search([
            ('start', '<=', dto),
            ('stop', '>=', date_start_str)
        ])
        events_lr = self.env['calendar.event'].search([
            ('start', '>=', date_start_str),
            ('stop', '<=', dto)
        ])
        events = (events_ll | events_lr) & events_raw
        return self._hcalendar_event_data(events)

    @api.model
    def get_hcalendar_settings(self):
        user_id = self.env['res.users'].browse(self.env.uid)
        type_move = user_id.pms_type_move
        return {
            'divide_rooms_by_capacity': user_id.pms_divide_rooms_by_capacity,
            'eday_week': user_id.pms_end_day_week,
            'eday_week_offset': user_id.pms_end_day_week_offset,
            'days': user_id.pms_default_num_days,
            'allow_invalid_actions': type_move == 'allow_invalid',
            'assisted_movement': type_move == 'assisted',
            'default_arrival_hour': self.env['ir.default'].sudo().get(
                'res.config.settings', 'default_arrival_hour'),
            'default_departure_hour': self.env['ir.default'].sudo().get(
                'res.config.settings', 'default_departure_hour'),
            'show_notifications': user_id.pms_show_notifications,
            'show_pricelist': user_id.pms_show_pricelist,
            'show_availability': user_id.pms_show_availability,
            'show_num_rooms': user_id.pms_show_num_rooms,
        }

    @api.model
    def get_hcalendar_all_data(self, dfrom, dto, withRooms=True):
        if not dfrom or not dto:
            raise ValidationError(_('Input Error: No dates defined!'))

        rooms = self.env['hotel.room'].search([], order='hcal_sequence ASC')
        json_res, json_res_tooltips = self.get_hcalendar_reservations_data(
            dfrom, dto, rooms)

        vals = {
            'rooms': withRooms and self._hcalendar_room_data(rooms) or [],
            'reservations': json_res,
            'tooltips': json_res_tooltips,
            'pricelist': self.get_hcalendar_pricelist_data(dfrom, dto),
            'restrictions': self.get_hcalendar_restrictions_data(dfrom, dto),
            'events': self.get_hcalendar_events_data(dfrom, dto),
        }

        return vals

    @api.multi
    def send_bus_notification(self, naction, ntype, ntitle=''):
        hotel_cal_obj = self.env['bus.hotel.calendar']
        for record in self:
            hotel_cal_obj.send_reservation_notification({
                'action': naction,
                'type': ntype,
                'title': ntitle,
                'id': record.room_id.id,
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
                'room_name': record.name,
                'partner_phone': record.partner_id.mobile
                                 or record.partner_id.phone or _('Undefined'),
                'state': record.state,
                'fix_days': record.splitted,
                'overbooking': record.overbooking,
                'price': record.folio_id.amount_total,
            })

    @api.model
    def swap_reservations(self, fromReservsIds, toReservsIds):
        from_reservs = self.env['hotel.reservation'].browse(fromReservsIds)
        to_reservs = self.env['hotel.reservation'].browse(toReservsIds)

        if not any(from_reservs) or not any(to_reservs):
            raise ValidationError(_("Invalid swap parameters"))

        max_from_persons = max(
            from_reservs.mapped(lambda x: x.adults))
        max_to_persons = max(
            to_reservs.mapped(lambda x: x.adults))

        from_room = from_reservs[0].room_id
        to_room = to_reservs[0].room_id
        from_overbooking = from_reservs[0].overbooking
        to_overbooking = to_reservs[0].overbooking

        if max_from_persons > to_room.capacity or \
                max_to_persons > from_room.capacity:
            raise ValidationError("Invalid swap operation: wrong capacity")

        for record in from_reservs:
            record.with_context({'ignore_avail_restrictions': True}).write({
                'room_id': to_room.id,
                'overbooking': to_overbooking,
            })
        for record in to_reservs:
            record.with_context({'ignore_avail_restrictions': True}).write({
                'room_id': from_room.id,
                'overbooking': from_overbooking,
            })

        return True

    @api.model
    def create(self, vals):
        reservation_id = super(HotelReservation, self).create(vals)
        reservation_id.send_bus_notification('create',
                                             'notify',
                                             _("Reservation Created"))
        return reservation_id

    @api.multi
    def write(self, vals):
        ret = super(HotelReservation, self).write(vals)
        if 'partner_id' in vals or 'checkin' in vals or \
                'checkout' in vals or 'product_id' in vals or \
                'adults' in vals or 'children' in vals or \
                'state' in vals or 'splitted' in vals or \
                'reserve_color' in vals or \
                'reserve_color_text' in vals or 'product_id' in vals or \
                'parent_reservation' in vals or 'overbooking' in vals:
            for record in self:
                record.send_bus_notification(
                    'write',
                    (record.state == 'cancelled') and 'warn' or 'notify',
                    (record.state == 'cancelled') and
                    _("Reservation Cancelled") or _("Reservation Changed")
                )
        elif not any(vals) or 'to_read' in vals or 'to_assign' in vals:
            self.send_bus_notification('write', 'noshow')
        return ret

    @api.multi
    def unlink(self):
        self.send_bus_notification('unlink',
                                   'warn',
                                   _("Reservation Deleted"))
        return super(HotelReservation, self).unlink()
