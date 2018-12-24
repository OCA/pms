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

    reserve_color = fields.Char(compute='_compute_color', string='Color',
                                store=True)
    reserve_color_text = fields.Char(compute='_compute_color', string='Color',
                                     store=True)

    """
    COMPUTE RESERVE COLOR ----------------------------------------------
    """

    @api.multi
    def _generate_color(self):
        self.ensure_one()

        reserv_color = '#FFFFFF'
        reserv_color_text = '#000000'
        user = self.env.user
        if self.reservation_type == 'staff':
            reserv_color = user.color_staff
            reserv_color_text = user.color_letter_staff
        elif self.reservation_type == 'out':
            reserv_color = user.color_dontsell
            reserv_color_text = user.color_letter_dontsell
        elif self.to_assign:
            reserv_color = user.color_to_assign
            reserv_color_text = user.color_letter_to_assign
        elif self.state == 'draft':
            reserv_color = user.color_pre_reservation
            reserv_color_text = user.color_letter_pre_reservation
        elif self.state == 'confirm':
            if self.folio_id.pending_amount <= 0:
                reserv_color = user.color_reservation_pay
                reserv_color_text = user.color_letter_reservation_pay
            else:
                reserv_color = user.color_reservation
                reserv_color_text = user.color_letter_reservation
        elif self.state == 'booking':
            if self.folio_id.pending_amount <= 0:
                reserv_color = user.color_stay_pay
                reserv_color_text = user.color_letter_stay_pay
            else:
                reserv_color = user.color_stay
                reserv_color_text = user.color_letter_stay
        else:
            if self.folio_id.pending_amount <= 0:
                reserv_color = user.color_checkout
                reserv_color_text = user.color_letter_checkout
            else:
                reserv_color = user.color_payment_pending
                reserv_color_text = user.color_letter_payment_pending
        return (reserv_color, reserv_color_text)

    @api.depends('state', 'reservation_type', 'folio_id.pending_amount', 'to_assign')
    def _compute_color(self):
        for record in self:
            colors = record._generate_color()
            record.update({
                'reserve_color': colors[0],
                'reserve_color_text': colors[1],
            })

    @api.model
    def _hcalendar_reservation_data(self, reservations):
        json_reservations = []
        json_reservation_tooltips = {}
        for reserv in reservations:
            json_reservations.append({
                'room_id': reserv.room_id.id,
                'id': reserv.id,
                'name': reserv.folio_id.closure_reason_id.name or _('Out of service') if reserv.folio_id.reservation_type == 'out'
                        else reserv.folio_id.partner_id.name,
                'adults': reserv.adults,
                'childrens': reserv.children,
                'checkin': reserv.checkin,
                'checkout': reserv.checkout,
                'folio_id': reserv.folio_id.id,
                'bgcolor': reserv.reserve_color,
                'color': reserv.reserve_color_text,
                'splitted': reserv.splitted,
                'parent_reservation': reserv.parent_reservation and reserv.parent_reservation.id or False,
                'read_only': False,  # Read-Only
                'fix_days': reserv.splitted,   # Fix Days
                'fix_room': False,  # Fix Rooms
                'overbooking': reserv.overbooking,
                'state': reserv.state,
                'real_dates': reserv.get_real_checkin_checkout()})
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
                reserv.id: {
                    'folio_name': reserv.folio_id.name,
                    'name': _('Out of service') if reserv.folio_id.reservation_type == 'out' else reserv.folio_id.partner_id.name,
                    'phone': reserv.mobile or reserv.phone or _('Phone not provided'),
                    'email': reserv.email or _('Email not provided'),
                    'room_type_name': reserv.room_type_id.name,
                    'adults': reserv.adults,
                    'children': reserv.children,
                    'checkin': reserv.checkin,
                    'checkout': reserv.checkout,
                    'arrival_hour': reserv.arrival_hour,
                    'departure_hour': reserv.departure_hour,
                    'num_split': num_split,
                    'amount_total': reserv.folio_id.amount_total,
                    'pending_amount': reserv.folio_id.pending_amount,
                    'amount_paid': reserv.folio_id.amount_total - reserv.folio_id.pending_amount,
                    'type': reserv.reservation_type or 'normal',
                    'out_service_description': reserv.out_service_description or
                                               _('No reason given'),
                    # TODO: Add Board Services and Extra Service as Cradle, Bed, ...
                }
            })
        return (json_reservations, json_reservation_tooltips)

    @api.model
    def _hcalendar_room_data(self, rooms):
        pricelist_id = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_pricelist_id')
        if pricelist_id:
            pricelist_id = int(pricelist_id)
        json_rooms = []
        for room in rooms:
            json_rooms.append({
                'id': room.id,
                'name': room.name,
                'capacity': room.capacity,
                'class_name': room.room_type_id.class_id.name,
                'class_id': room.room_type_id.class_id.id,
                'shared': room.shared_room,
                'price': room.room_type_id
                         and ['pricelist', room.room_type_id.id, pricelist_id,
                              room.room_type_id.name] or 0,
                'room_type_name': room.room_type_id.name,
                'room_type_id': room.room_type_id.id,
                'floor_id': room.floor_id.id,
                'amentity_ids': room.room_type_id.room_amenity_ids.ids,
            })
        return json_rooms

    @api.model
    def _hcalendar_calendar_data(self, calendars):
        json_calendars = []
        for calendar in calendars:
            json_calendars.append({
                'id': calendar.id,
                'name': calendar.name,
                'segmentation_ids': calendar.segmentation_ids.ids,
                'location_ids': calendar.location_ids.ids,
                'amenity_ids': calendar.amenity_ids.ids,
                'room_type_ids': calendar.room_type_ids.ids,
            })
        return json_calendars

    @api.model
    def _hcalendar_event_data(self, events):
        json_events = []
        for event in events:
            json_events.append({
                'id': event.id,
                'name': event.name,
                'date': event.start,
                'location': event.location,
            })
        return json_events

    @api.model
    def get_hcalendar_reservations_data(self, dfrom, dto, rooms):
        date_start = fields.Date.from_string(dfrom) - timedelta(days=1)
        date_start_str = date_start.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        reservations_raw = self.env['hotel.reservation'].search(
            [('room_id', 'in', rooms.ids)],
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
            'res.config.settings', 'default_pricelist_id')
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
            'res.config.settings', 'default_restriction_id')
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
                    ('date', '=', ndate_str),
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
        calendars = self.env['hotel.calendar'].search([])
        json_res, json_res_tooltips = self.get_hcalendar_reservations_data(
            dfrom, dto, rooms)

        vals = {
            'rooms': withRooms and self._hcalendar_room_data(rooms) or [],
            'reservations': json_res,
            'tooltips': json_res_tooltips,
            'pricelist': self.get_hcalendar_pricelist_data(dfrom, dto),
            'restrictions': self.get_hcalendar_restrictions_data(dfrom, dto),
            'events': self.get_hcalendar_events_data(dfrom, dto),
            'calendars': self._hcalendar_calendar_data(calendars)
        }

        return vals

    @api.multi
    def generate_bus_values(self, naction, ntype, ntitle=''):
        self.ensure_one()
        return {
            'action': naction,
            'type': ntype,
            'title': ntitle,
            'room_id': self.room_id.id,
            'reserv_id': self.id,
            'partner_name': (self.closure_reason_id.name or _('Out of service'))
                            if self.reservation_type == 'out' else self.partner_id.name,
            'adults': self.adults,
            'children': self.children,
            'checkin': self.checkin,
            'checkout': self.checkout,
            'arrival_hour': self.arrival_hour,
            'departure_hour': self.departure_hour,
            'folio_id': self.folio_id.id,
            'reserve_color': self.reserve_color,
            'reserve_color_text': self.reserve_color_text,
            'splitted': self.splitted,
            'parent_reservation': self.parent_reservation and
                                  self.parent_reservation.id or 0,
            'room_name': self.room_id.name,
            'room_type_name': self.room_type_id.name,
            'partner_phone': self.partner_id.mobile
                             or self.partner_id.phone or _('Undefined'),
            'partner_email': self.partner_id.email or _('Undefined'),
            'state': self.state,
            'fix_days': self.splitted,
            'overbooking': self.overbooking,
            'amount_total': self.folio_id.amount_total,
            'pending_amount': self.folio_id.pending_amount,
            'amount_paid': self.folio_id.amount_total - self.folio_id.pending_amount,
            'reservation_type': self.reservation_type or 'normal',
            'closure_reason_id': self.closure_reason_id,
            'out_service_description': self.out_service_description or _('No reason given'),
            'real_dates': self.get_real_checkin_checkout(),
        }

    @api.multi
    def send_bus_notification(self, naction, ntype, ntitle=''):
        hotel_cal_obj = self.env['bus.hotel.calendar']
        for record in self:
            hotel_cal_obj.send_reservation_notification(
                record.generate_bus_values(naction, ntype, ntitle))

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
        _logger.info("RESERV WRITE")
        if 'partner_id' in vals or 'checkin' in vals or \
                'checkout' in vals or 'product_id' in vals or \
                'adults' in vals or 'children' in vals or \
                'state' in vals or 'splitted' in vals or \
                'closure_reason_id' in vals or 'out_service_description' in vals or \
                'reservation_type' in vals or \
                'reserve_color' in vals or \
                'reserve_color_text' in vals or 'price_total' in vals or \
                'parent_reservation' in vals or 'overbooking' in vals or \
                'room_type_id' in vals:
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
