# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import json
from datetime import datetime, timedelta
from dateutil import tz
from odoo import fields, api
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo.addons.hotel_channel_connector_wubook.components.backend_adapter import (
    DEFAULT_WUBOOK_DATE_FORMAT,
    DEFAULT_WUBOOK_DATETIME_FORMAT,
    WUBOOK_STATUS_BAD)
_logger = logging.getLogger(__name__)


class HotelReservationImporter(Component):
    _inherit = 'channel.hotel.reservation.importer'

    @api.model
    def fetch_booking(self, channel_reservation_id):
        try:
            results = self.backend_adapter.fetch_booking(channel_reservation_id)
        except ChannelConnectorError as err:
            self.create_issue(
                section='reservation',
                internal_message=str(err),
                channel_message=err.data['message'])
            return False
        else:
            if any(results):
                processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
                    self._generate_reservations(results)
                if any(processed_rids):
                    self.backend_adapter.mark_bookings(list(set(processed_rids)))
                # Update Odoo availability (don't wait for wubook)
                # FIXME: This cause abuse service in first import!!
                if checkin_utc_dt and checkout_utc_dt:
                    self.backend_adapter.fetch_rooms_values(
                        checkin_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                        checkout_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT))
        return True

    def fetch_new_bookings(self):
        count = 0
        try:
            results = self.backend_adapter.fetch_new_bookings()
        except ChannelConnectorError as err:
            self.create_issue(
                section='reservation',
                internal_message=str(err),
                channel_message=err.data['message'])
        else:
            if any(results):
                processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
                    self._generate_reservations(results)
                if any(processed_rids):
                    uniq_rids = list(set(processed_rids))
                    self.backend_adapter.mark_bookings(uniq_rids)
                    count = len(uniq_rids)
                # Update Odoo availability (don't wait for wubook)
                # FIXME: This cause abuse service in first import!!
                if checkin_utc_dt and checkout_utc_dt:
                    self.backend_adapter.fetch_rooms_values(
                        checkin_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                        checkout_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT))
            return count

    def fetch_bookings(self, dfrom, dto):
        count = 0
        try:
            results = self.backend_adapter.fetch_bookings(dfrom, dto)
        except ChannelConnectorError as err:
            self.create_issue(
                section='reservation',
                internal_message=str(err),
                channel_message=err.data['message'])
        else:
            if any(results):
                processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
                    self._generate_reservations(results)
                if any(processed_rids):
                    uniq_rids = list(set(processed_rids))
                    count = len(uniq_rids)
                # Update Odoo availability (don't wait for wubook)
                # FIXME: This cause abuse service in first import!!
                if checkin_utc_dt and checkout_utc_dt:
                    self.backend_adapter.fetch_rooms_values(
                        checkin_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                        checkout_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT))
            return count

    @api.model
    def _get_board_services(self, broom, book, room_type_bind, persons):
        board_service = None
        board_service_amount = 0.0
        # WuBook Reservation Engine
        if book['id_channel'] == 0:
            board_service = room_type_bind.board_service_room_type_ids.filtered(
                lambda r: r.channel_service == book['boards'][room_type_bind.external_id]).id or None
        # Booking.com Reservation Engine
        elif book['id_channel'] == 2:
            detected_board = book.get('ancillary', {}).get('Detected Board') or None
            # Board services can be included in the rate plan and detected by the WuBook API
            if detected_board and detected_board != 'nb':
                board_service = room_type_bind.board_service_room_type_ids.filtered(
                    lambda r: r.channel_service == detected_board).id or None
                # NOTE: Board services are managed by day and by person
                board_service_amount = board_service and room_type_bind.board_service_room_type_ids.browse(
                    board_service).amount * persons
            # else:
            #     detected_addons = broom.get('ancillary', {}).get('addons') or []
            #     # Board services can be included as a list of addons where the price is broken down by day and service
            #     boards_map = {"Breakfast": "bb"}
            #     for addon in detected_addons:
            #         detected_board = addon.get('type') in boards_map and boards_map[addon.get('type')]
            #         board_service = room_type_bind.board_service_room_type_ids.filtered(
            #             lambda r: r.channel_service == detected_board).id or None
            #         # TODO: what to do if more than one addon is shipped in this array ¿?

        # TODO: Expedia.com Reservation Engine
        return board_service, board_service_amount

    @api.model
    def _generate_booking_vals(self, broom, crcode, rcode, room_type_bind,
                               split_booking, dates_checkin, dates_checkout, real_checkin, real_checkout, book):
        is_cancellation = book['status'] in WUBOOK_STATUS_BAD
        tax_inclusive = True
        persons = room_type_bind.ota_capacity
        # Info about the occupancy of each booked room (it can be empty)
        # BUG: occupancy includes children... Review adults by OTA
        # occupancy = next((item for item in book['rooms_occupancies'] if item["id"] == broom['room_id']), False)
        # if occupancy:
        #     persons = occupancy['occupancy']
        # Dates
        real_checkin_str = real_checkin.strftime(
            DEFAULT_SERVER_DATETIME_FORMAT)
        real_checkout_str = real_checkout.strftime(
            DEFAULT_SERVER_DATETIME_FORMAT)
        checkin_str = dates_checkin[0].strftime(
            DEFAULT_SERVER_DATETIME_FORMAT)
        checkout_str = dates_checkout[0].strftime(
            DEFAULT_SERVER_DATETIME_FORMAT)
        # Parse 'ancyllary' info
        if 'ancillary' in broom:
            if 'guests' in broom['ancillary']:
                persons = min(broom['ancillary']['guests'], persons)
            if 'tax_inclusive' in broom['ancillary'] and not broom['ancillary']['tax_inclusive']:
                _logger.info("--- Incoming Reservation without taxes included!")
                tax_inclusive = False
        # WuBook rate plan
        rate_id = None
        # Information about Board Services
        board_service, board_service_amount = self._get_board_services(broom, book, room_type_bind, persons)
        # Generate Reservation Day Lines
        reservation_lines = []
        tprice = 0.0
        for brday in broom['roomdays']:
            wndate = datetime.strptime(
                brday['day'],
                DEFAULT_WUBOOK_DATE_FORMAT
            ).replace(tzinfo=tz.gettz('UTC')).date()
            if dates_checkin[0].date() <= wndate < dates_checkout[0].date():
                amount_day_tax = 0
                if not tax_inclusive:
                    price_subtotal = book['amount'] - broom['ancillary']['taxes']
                    day_tax_weigh = brday['price'] * 100 / price_subtotal
                    amount_day_tax = broom['ancillary']['taxes'] * day_tax_weigh / 100
                room_day_price = brday['price'] + amount_day_tax
                reservation_lines.append((0, False, {
                    'date': wndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'price': room_day_price - board_service_amount,
                }))
                tprice += room_day_price
            rate_id = brday['rate_id']
            # TODO: Review different pricelist in the different booked rooms (folio in Odoo)

        parity_rate_id = self.env['channel.backend'].search([
            ('id', '=', self.backend_record.id)
        ]).wubook_parity_pricelist_id
        # WuBook API rate_id ( booked pricing plan: -1 Unknown, 0 WuBook Parity or WuBook id of the plan)
        if rate_id > 0:
            rate_id = self.env['channel.product.pricelist'].search([
                ('backend_id', '=', self.backend_record.id),
                ('external_id', '=', rate_id)
            ]).odoo_id or None
        elif rate_id == 0:
            rate_id = parity_rate_id
        else:
            rate_id = None
        if not rate_id:
            # Unknown rate < 0 OR mapped incorrectly in Odoo
            self.create_issue(
                section='reservation',
                internal_message="Reservation imported with unknown \
                                pricelist (established by default)",
                channel_object_id=book['reservation_code'])
        rate_id = rate_id and rate_id.id or parity_rate_id.id
        # Get OTA
        ota_id = self.env['channel.ota.info'].search([
            ('backend_id', '=', self.backend_record.id),
            ('ota_id', '=', str(book['id_channel'])),
        ], limit=1)
        modified_codes = ''
        if book['modified_reservations']:
            modified_codes = ' '.join(str(e) for e in book['modified_reservations'])
        binding_vals = {
            'backend_id': self.backend_record.id,
            'external_id': rcode,
            'ota_id': ota_id and ota_id.id,
            'ota_reservation_id': crcode,
            'channel_status': str(book['status']),
            'channel_raw_data': json.dumps(book),
            'channel_modified': book['was_modified'],
            'channel_total_amount': book['amount'],
            'modified_reservations': modified_codes,
        }
        vals = {
            'real_checkin': real_checkin_str,
            'real_checkout': real_checkout_str,
            'checkin': checkin_str,
            'checkout': checkout_str,
            'adults': persons,
            'children': book['children'],
            'pricelist_id': rate_id,
            'reservation_line_ids': reservation_lines,
            'board_service_room_id': board_service,
            'to_assign': True,
            'state': is_cancellation and 'cancelled' or 'confirm',
            'room_type_id': room_type_bind.odoo_id.id,
            'splitted': split_booking,
            'name': room_type_bind and room_type_bind.name,
            'channel_bind_ids': [(0, False, binding_vals)],
        }

        return vals

    @api.model
    def _generate_partner_vals(self, book):
        country_id = self.env['res.country'].search([
            ('code', '=', str(book['customer_country']))
        ], limit=1)
        # lang = self.env['res.lang'].search([('code', '=', book['customer_language_iso'])], limit=1)
        return {
            'name': "%s, %s" % (book['customer_surname'], book['customer_name']),
            'country_id': country_id and country_id.id,
            'city': book['customer_city'],
            'phone': book['customer_phone'],
            'zip': book['customer_zip'],
            'street': book['customer_address'],
            'email': book['customer_mail'],
            'unconfirmed': True,
            # 'lang': lang and lang.id,
        }

    def _get_book_dates(self, book):
        default_arrival_hour = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_arrival_hour')
        default_departure_hour = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_departure_hour')

        checkin = "%s %s" % (book['date_arrival'], default_arrival_hour)
        checkin_utc_dt = datetime.strptime(checkin, DEFAULT_WUBOOK_DATETIME_FORMAT).replace(
            tzinfo=tz.gettz('UTC'))

        checkout = "%s %s" % (book['date_departure'], default_departure_hour)
        checkout_utc_dt = datetime.strptime(checkout, DEFAULT_WUBOOK_DATETIME_FORMAT).replace(
            tzinfo=tz.gettz('UTC'))

        return checkin_utc_dt, checkout_utc_dt

    def _force_update_availability_wubook(self, binding):
        # WuBook always add +1 in the channel manager for cancelled reservation
        # However, the quota in Odoo has preference in the availability
        cancelled_dates = binding.reservation_line_ids.mapped('date')
        channel_availability = self.env['channel.hotel.room.type.availability'].search([
            ('backend_id', '=', binding.backend_id.id),
            ('date', 'in', cancelled_dates)
        ])
        channel_availability.write({'channel_pushed': False})
        # Force an update with the correct availability
        channel_availability.push_availability(binding.backend_id)

    def _force_update_availability_wubook(self, binding):
        # WuBook always add +1 in the channel manager for cancelled reservation
        # However, the quota in Odoo has preference in the availability
        cancelled_dates = binding.reservation_line_ids.mapped('date')
        channel_availability = self.env['channel.hotel.room.type.availability'].search([
            ('backend_id', '=', binding.backend_id.id),
            ('date', 'in', cancelled_dates)
        ])
        channel_availability.write({'channel_pushed': False})
        # Force an update with the correct availability
        channel_availability.push_availability(binding.backend_id)

    def _force_update_availability_wubook(self, binding):
        # WuBook always add +1 in the channel manager for cancelled reservation
        # However, the quota in Odoo has preference in the availability
        cancelled_dates = binding.reservation_line_ids.mapped('date')
        channel_availability = self.env['channel.hotel.room.type.availability'].search([
            ('backend_id', '=', binding.backend_id.id),
            ('date', 'in', cancelled_dates)
        ])
        channel_availability.write({'channel_pushed': False})
        # Force an update with the correct availability
        channel_availability.push_availability(binding.backend_id)

    def _update_reservation_binding(self, binding, book):
        is_cancellation = book['status'] in WUBOOK_STATUS_BAD
        binding.with_context({'connector_no_export': True}).write({
            'channel_raw_data': json.dumps(book),
            'channel_status': str(book['status']),
            'channel_status_reason': book.get('status_reason', ''),
            'to_assign': True,
            'customer_notes': book['customer_notes'],
            'channel_total_amount': book['amount'],
        })
        if binding.partner_id.unconfirmed:
            binding.partner_id.write(
                self._generate_partner_vals(book)
            )
        if is_cancellation:
            binding.odoo_id.with_context({
                'connector_no_export': True,
                'ota_limits': False}).action_cancel()
            self._force_update_availability_wubook(binding)
        elif binding.state == 'cancelled':
            binding.with_context({
                'connector_no_export': True,
            }).write({
                'discount': 0.0,
                'state': 'confirm',
            })

    @api.model
    def wubook_modification(self, reservations, book):
        channel_room_type_obj = self.env['channel.hotel.room.type']
        checkin_utc_dt, checkout_utc_dt = self._get_book_dates(book)
        checkin = checkin_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        checkout = checkout_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        new_books = []
        for broom in book['booked_rooms']:
            reservation = False
            room_type_bind = channel_room_type_obj.search([
                ('backend_id', '=', self.backend_record.id),
                ('external_id', '=', broom['room_id'])
            ], limit=1)
            if reservations:
                #REVIEW: modified_reservations is possibly useless (used_room nerver
                # it will match with rooms in reservations recordset paramenter
                modified_codes = ' '.join(str(e) for e in book['modified_reservations'])
                modified_reservations = self.env['channel.hotel.reservation'].search([
                    ('modified_reservations', 'ilike', modified_codes),
                ])
                used_rooms = []
                if modified_reservations:
                    used_rooms = modified_reservations.mapped('room_id.id')
                reservation = reservations.filtered(
                    lambda res: res.room_type_id == room_type_bind.odoo_id and
                    res.checkin == checkin and res.checkout == checkout and
                    res.room_id.id not in used_rooms
                    )
            if reservation:
                reservation = reservation[0]
                vals = {
                    'channel_raw_data': json.dumps(book),
                    'channel_status': str(book['status']),
                    'channel_status_reason': book.get('status_reason', ''),
                    'to_assign': True,
                    'customer_notes': book['customer_notes'],
                    'channel_total_amount': book['amount'],
                    'modified_reservations': modified_codes,
                    'external_id': str(book['reservation_code']),
                }
                reservation.odoo_id.with_context({
                    'connector_no_export': True,
                    'ota_limits': False,
                    'no_penalty': True}).confirm()
                reservation.with_context({'connector_no_export': True}).write(vals)
                reservations -= reservation
            else:
                new_books.append(broom)
                # Review quota if new reservation is a modification not recognized in this method
                # because quota is __always__ decreased when creating reservation, even in the overlapped days
        return new_books, reservations


    # FIXME: Super big method!!! O_o
    @api.model
    def _generate_reservations(self, bookings):
        _logger.info("==[CHANNEL->ODOO]==== READING BOOKING ==")
        _logger.info(bookings)
        # Get user timezone
        res_partner_obj = self.env['res.partner']
        channel_reserv_obj = self.env['channel.hotel.reservation']
        hotel_folio_obj = self.env['hotel.folio']
        channel_room_type_obj = self.env['channel.hotel.room.type']
        # Space for store some data for construct folios
        processed_rids = []
        failed_reservations = []
        checkin_utc_dt = False
        checkout_utc_dt = False
        split_booking = False
        for book in bookings:   # This create a new folio
            new_books = book['booked_rooms']
            splitted_map = {}
            rcode = str(book['reservation_code'])
            crcode = str(book['channel_reservation_code']) \
                if book['channel_reservation_code'] else 'undefined'

            # Can't process failed reservations
            #  (for example set a invalid new reservation and receive in
            # the same transaction an cancellation)
            if crcode in failed_reservations:
                self.create_issue(
                    section='reservation',
                    internal_message="Can't process a reservation that previously failed!",
                    channel_object_id=book['reservation_code'])
                continue

            checkin_utc_dt, checkout_utc_dt = self._get_book_dates(book)

            # Search Folio. If exists.
            folio_id = False
            if crcode != 'undefined':
                reserv_bind = channel_reserv_obj.search([
                    ('backend_id', '=', self.backend_record.id),
                    ('ota_reservation_id', '=', crcode),
                ], limit=1)
                if reserv_bind:
                    folio_id = reserv_bind.folio_id
            else:
                reserv_bind = channel_reserv_obj.search([
                    ('backend_id', '=', self.backend_record.id),
                    ('external_id', '=', rcode),
                ], limit=1)
                if reserv_bind:
                    folio_id = reserv_bind.folio_id

            if len(book['modified_reservations']) > 0:
                is_cancellation = book['status'] in WUBOOK_STATUS_BAD
                if book['was_modified'] and is_cancellation:
                    processed_rids.append(rcode)
                    continue
                elif not is_cancellation:
                    old_reservations = False
                    reservations = self.env['channel.hotel.reservation'].search([
                        ('external_id', 'in', book['modified_reservations']),
                        ('backend_id', '=', self.backend_record.id)
                    ])
                    if reservations:
                        new_books, old_reservations = self.wubook_modification(reservations, book)
                    if old_reservations:
                        for res in old_reservations:
                            res.odoo_id.with_context({
                                'connector_no_export': True,
                                'ota_limits': False,
                                'no_penalty': True}).action_cancel()
                            self._force_update_availability_wubook(res.channel_bind_ids[0])
                    if len(new_books) == 0:
                        processed_rids.append(rcode)
                        continue

            # Need update reservations?
            is_cancellation = book['status'] in WUBOOK_STATUS_BAD
            if not book['was_modified'] and is_cancellation:
                reservs_processed = False
                reservs_binds = channel_reserv_obj.search([
                    ('backend_id', '=', self.backend_record.id),
                    ('external_id', '=', rcode),
                ])
                for reserv_bind in reservs_binds:
                    self._update_reservation_binding(reserv_bind, book)
                    reservs_processed = True
                # Do Nothing if already processed 'external_id'
                if reservs_processed:
                    processed_rids.append(rcode)
                    continue

            # Create new Customer
            partner_id = res_partner_obj.create(self._generate_partner_vals(book))

            reservations = []
            used_rooms = []
            # Iterate booked rooms
            for broom in new_books:
                room_type_bind = channel_room_type_obj.search([
                    ('backend_id', '=', self.backend_record.id),
                    ('external_id', '=', broom['room_id'])
                ], limit=1)
                if not room_type_bind:
                    self.create_issue(
                        section='reservation',
                        internal_message="Can't found any room type associated to '%s' \
                                            in this hotel" % book['rooms'],
                        channel_object_id=book['reservation_code'])
                    failed_reservations.append(crcode)
                    continue
                if not any(room_type_bind.room_ids):
                    self.create_issue(
                        section='reservation',
                        internal_message="Selected room type (%s) doesn't have any \
                                            real room" % book['rooms'],
                        channel_object_id=book['reservation_code'])
                    failed_reservations.append(crcode)
                    continue

                dates_checkin = [checkin_utc_dt, False]
                dates_checkout = [checkout_utc_dt, False]
                split_booking = False
                split_booking_parent = False
                # This perhaps create splitted reservation
                while dates_checkin[0]:
                    vals = self._generate_booking_vals(
                        broom,
                        crcode,
                        rcode,
                        room_type_bind,
                        split_booking,
                        dates_checkin,
                        dates_checkout,
                        checkin_utc_dt,
                        checkout_utc_dt,
                        book,
                    )
                    #
                    # if vals['price_unit'] != book['amount']:
                    #     bs = self.env['hotel.board.service.room.type'].browse(vals['board_service_room_id'])
                    #     price_room_services_set = vals['price_unit'] + (bs.amount * len(broom['roomdays']))
                    #     vals.update({'unconfirmed_channel_price': True})
                    #     # check if difference is owing to misconfigured board services
                    #     if price_room_services_set != book['amount']:
                    #         internal_reason = 'Please, review the board services included in the reservation.'
                    #         self.create_issue(
                    #             section='reservation',
                    #             internal_message="Invalid reservation total price! %.2f (calculated) != %.2f (wubook) %s" % (
                    #                 vals['price_unit'], book['amount'], internal_reason),
                    #             channel_object_id=book['reservation_code'])
                    #     # TODO: Add other reasons in case of need


                    free_rooms = room_type_bind.odoo_id.check_availability_room_type(
                        vals['checkin'],
                        (fields.Date.from_string(vals['checkout']) -
                            timedelta(days=1)).strftime(
                                DEFAULT_SERVER_DATE_FORMAT
                                ),
                        room_type_id=room_type_bind.odoo_id.id,
                        notthis=used_rooms)
                    if any(free_rooms):
                        vals.update({
                            'room_type_id': room_type_bind.odoo_id.id,
                            'name': free_rooms[0].name,
                        })
                        reservations.append((0, False, vals))
                        used_rooms.append(free_rooms[0].id)

                        if split_booking:
                            if not split_booking_parent:
                                split_booking_parent = len(reservations)
                            else:
                                splitted_map.setdefault(
                                    split_booking_parent,
                                    []).append(len(reservations))
                                # sql_constraint 'unique(backend_id, external_id)'
                                del reservations[-1][2]['channel_bind_ids']
                        dates_checkin = [dates_checkin[1], False]
                        dates_checkout = [dates_checkout[1], False]
                    else:
                        date_diff = (dates_checkout[0].replace(
                            hour=0, minute=0, second=0,
                            microsecond=0) -
                                     dates_checkin[0].replace(
                                         hour=0, minute=0, second=0,
                                         microsecond=0)).days
                        if date_diff <= 0:
                            if split_booking:
                                if split_booking_parent:
                                    del reservations[split_booking_parent-1:]
                                    if split_booking_parent in splitted_map:
                                        del splitted_map[split_booking_parent]
                            # Can't found space for reservation: Overbooking
                            vals = self._generate_booking_vals(
                                broom,
                                crcode,
                                rcode,
                                room_type_bind,
                                False,
                                (checkin_utc_dt, False),
                                (checkout_utc_dt, False),
                                checkin_utc_dt,
                                checkout_utc_dt,
                                book,
                            )
                            vals.update({
                                'room_type_id': room_type_bind.odoo_id.id,
                                'name': room_type_bind.name,
                                'overbooking': True,
                            })
                            reservations.append((0, False, vals))
                            self.create_issue(
                                section='reservation',
                                internal_message="Reservation imported with overbooking state",
                                channel_object_id=rcode,
                                dfrom=vals['checkin'], dto=vals['checkout'])
                            dates_checkin = [False, False]
                            dates_checkout = [False, False]
                            split_booking = False
                        else:
                            split_booking = True
                            dates_checkin = [
                                dates_checkin[0],
                                dates_checkin[0] + timedelta(days=date_diff-1)
                            ]
                            dates_checkout = [
                                dates_checkout[0] - timedelta(days=1),
                                checkout_utc_dt
                            ]

            # Create Splitted Issue Information
            if split_booking:
                self.create_issue(
                    section='reservation',
                    internal_message="Reservation Splitted",
                    channel_object_id=rcode)

            # Create Folio
            if not any(failed_reservations) and any(reservations):
                # TODO: Improve 'addons_list' & discounts
                addons = str(book['addons_list']) if any(book['addons_list']) else ''
                discounts = book.get('discount', '')
                vals = {
                    'reservation_ids': reservations,
                    'customer_notes': "%s\nADDONS:\n%s\nDISCOUNT:\n%s" % (
                        book['customer_notes'], addons, discounts),
                    'channel_type': 'web',
                }
                _logger.info("==[CHANNEL->ODOO]==== CREATING/UPDATING FOLIO ==")
                _logger.info(reservations)
                if folio_id:
                    folio_id.with_context({
                        'connector_no_export': True}).write(vals)
                else:
                    vals.update({
                        'partner_id': partner_id.id,
                        'wseed': book['sessionSeed']
                    })
                    folio_id = hotel_folio_obj.with_context({
                        'connector_no_export': True}).create(vals)


                # Update Reservation Spitted Parents
                sorted_rlines = folio_id.reservation_ids.sorted(key='id')
                for k_pid, v_pid in splitted_map.items():
                    preserv = sorted_rlines[k_pid-1]
                    for pid in v_pid:
                        creserv = sorted_rlines[pid-1]
                        creserv.parent_reservation = preserv.id
                # Bind reservations
                rlines = sorted_rlines = folio_id.reservation_ids
                for rline in rlines:
                    for rline_bind in rline.channel_bind_ids:
                        self.binder.bind(rline_bind.external_id, rline_bind)
                    # TODO: Imp importer, refactoring method
                    # Force to_assign = true (fix the to_assign splitted reservations)
                    rline.update({'to_assign': True})
                    # Force to update avail on splitteds sections
                    if rline.parent_reservation:
                        # This break with multi channels by room type
                        backend_id = self.env['channel.hotel.room.type'].search([
                            ('odoo_id', '=', rline.room_type_id.id)
                        ]).backend_id
                        self.env['channel.hotel.room.type.availability'].sudo().refresh_availability(
                            checkin=rline.real_checkin,
                            checkout=rline.real_checkout,
                            backend_id=backend_id.id,
                            room_type_id=rline.room_type_id.id,
                            from_channel=True,)

                processed_rids.append(rcode)
        return (processed_rids, any(failed_reservations),
                checkin_utc_dt, checkout_utc_dt)
