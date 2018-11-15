# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import json
from datetime import datetime, timedelta
from dateutil import tz
from odoo.exceptions import ValidationError
from odoo import fields, api, _
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo.addons.hotel_channel_connector.components.backend_adapter import (
    DEFAULT_WUBOOK_DATE_FORMAT,
    DEFAULT_WUBOOK_DATETIME_FORMAT,
    WUBOOK_STATUS_BAD)
_logger = logging.getLogger(__name__)


class HotelReservationImporter(Component):
    _name = 'channel.hotel.reservation.importer'
    _inherit = 'hotel.channel.importer'
    _apply_on = ['channel.hotel.reservation']
    _usage = 'hotel.reservation.importer'

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

    @api.model
    def _generate_booking_vals(self, broom, crcode, rcode, room_type_bind,
                               split_booking, dates_checkin, dates_checkout, book):
        is_cancellation = book['status'] in WUBOOK_STATUS_BAD
        tax_inclusive = True
        persons = room_type_bind.channel_capacity
        # Dates
        checkin_str = dates_checkin[0].strftime(
            DEFAULT_SERVER_DATETIME_FORMAT)
        checkout_str = dates_checkout[0].strftime(
            DEFAULT_SERVER_DATETIME_FORMAT)
        # Parse 'ancyllary' info
        if 'ancillary' in broom:
            if 'guests' in broom['ancillary']:
                persons = broom['ancillary']['guests']
            if 'tax_inclusive' in broom['ancillary'] and not broom['ancillary']['tax_inclusive']:
                _logger.info("--- Incoming Reservation without taxes included!")
                tax_inclusive = False
        # Generate Reservation Day Lines
        reservation_lines = []
        tprice = 0.0
        for brday in broom['roomdays']:
            wndate = datetime.strptime(
                brday['day'],
                DEFAULT_WUBOOK_DATE_FORMAT
            ).replace(tzinfo=tz.gettz('UTC'))
            if dates_checkin[0] >= wndate <= (dates_checkout[0] - timedelta(days=1)):
                # HOT-FIX: Hard-Coded Tax 10%
                room_day_price = round(brday['price'] * 1.1, 2) if not tax_inclusive else brday['price']
                reservation_lines.append((0, False, {
                    'date': wndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'price': room_day_price,
                }))
                tprice += room_day_price
        # Get OTA
        ota_id = self.env['channel.ota.info'].search([
            ('backend_id', '=', self.backend_record.id),
            ('ota_id', '=', str(book['id_channel'])),
        ], limit=1)

        vals = {
            'backend_id': self.backend_record.id,
            'checkin': checkin_str,
            'checkout': checkout_str,
            'adults': persons,
            'children': book['children'],
            'reservation_lines': reservation_lines,
            'price_unit': tprice,
            'to_assign': True,
            'wrid': rcode,
            'ota_id': ota_id and ota_id.id,
            'wchannel_reservation_code': crcode,
            'channel_status': str(book['status']),
            'to_read': True,
            'state': is_cancellation and 'cancelled' or 'draft',
            'room_type_id': room_type_bind.odoo_id.id,
            'splitted': split_booking,
            'wbook_json': json.dumps(book),
            'wmodified': book['was_modified'],
            'product_id': room_type_bind and room_type_bind.product_id.id,
            'name': room_type_bind and room_type_bind.name,
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
        tz_hotel = self.env['ir.default'].sudo().get('res.config.settings', 'tz_hotel')
        default_arrival_hour = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_arrival_hour')
        default_departure_hour = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_departure_hour')

        # Get dates for the reservation (GMT->UTC)
        arr_hour = default_arrival_hour if book['arrival_hour'] == "--" \
            else book['arrival_hour']
        # HOT-FIX: Wubook 24:00 hour
        arr_hour_s = arr_hour.split(':')
        if arr_hour_s[0] == '24':
            arr_hour_s[0] = '00'
            arr_hour = ':'.join(arr_hour_s)
        checkin = "%s %s" % (book['date_arrival'], arr_hour)
        checkin_dt = datetime.strptime(checkin, DEFAULT_WUBOOK_DATETIME_FORMAT).replace(
            tzinfo=tz.gettz(str(tz_hotel)))
        checkin_utc_dt = checkin_dt.astimezone(tz.gettz('UTC'))
        #checkin = checkin_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        checkout = "%s %s" % (book['date_departure'],
                              default_departure_hour)
        checkout_dt = datetime.strptime(checkout, DEFAULT_WUBOOK_DATETIME_FORMAT).replace(
            tzinfo=tz.gettz(str(tz_hotel)))
        checkout_utc_dt = checkout_dt.astimezone(tz.gettz('UTC'))
        #checkout = checkout_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        return (checkin_utc_dt, checkout_utc_dt)

    def _update_reservation_binding(self, binding, book):
        is_cancellation = book['status'] in WUBOOK_STATUS_BAD
        binding.with_context({'connector_no_export': True}).write({
            'channel_raw_data': json.dumps(book),
            'channel_status': str(book['status']),
            'channel_status_reason': book.get('status_reason', ''),
            'to_read': True,
            'to_assign': True,
            'price_unit': book['amount'],
            'customer_notes': book['customer_notes'],
        })
        if binding.partner_id.unconfirmed:
            binding.partner_id.write(
                self._generate_partner_vals(book)
            )
        if is_cancellation:
            binding.with_context({
                'connector_no_export': True}).action_cancel()
        elif binding.state == 'cancelled':
            binding.with_context({
                'connector_no_export': True,
            }).write({
                'discount': 0.0,
                'state': 'confirm',
            })


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
                    internal_emssage="Can't process a reservation that previusly failed!",
                    channel_object_id=book['reservation_code'])
                continue

            checkin_utc_dt, checkout_utc_dt = self._get_book_dates(book)

            # Search Folio. If exists.
            folio_id = False
            if crcode != 'undefined':
                reserv_bind = channel_reserv_obj.search([
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

            # Need update reservations?
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

            # Search Customer
            customer_mail = book.get('customer_mail', False)
            partner_id = False
            if customer_mail:
                partner_id = res_partner_obj.search([
                    ('email', '=', customer_mail)
                ], limit=1)
            if not partner_id:
                partner_id = res_partner_obj.create(self._generate_partner_vals(book))

            reservations = []
            used_rooms = []
            # Iterate booked rooms
            for broom in book['booked_rooms']:
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
                        book,
                    )
                    if vals['price_unit'] != book['amount']:
                        self.create_issue(
                            section='reservation',
                            internal_message="Invalid reservation total price! %.2f (calculated) != %.2f (wubook)" % (vals['price_unit'], book['amount']),
                            channel_object_id=book['reservation_code'])

                    free_rooms = room_type_bind.odoo_id.check_availability_room_type(
                        vals['checkin'],
                        vals['checkout'],
                        room_type_id=room_type_bind.odoo_id.id,
                        notthis=used_rooms)
                    if any(free_rooms):
                        vals.update({
                            'product_id': room_type_bind.product_id.id,
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
                                book,
                            )
                            vals.update({
                                'product_id': room_type_bind.product_id.id,
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
                    'room_lines': reservations,
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
                sorted_rlines = folio_id.room_lines.sorted(key='id')
                for k_pid, v_pid in splitted_map.items():
                    preserv = sorted_rlines[k_pid-1]
                    for pid in v_pid:
                        creserv = sorted_rlines[pid-1]
                        creserv.parent_reservation = preserv.id

                # Bind reservations
                rlines = sorted_rlines = folio_id.room_lines
                for rline in rlines:
                    for rline_bind in rline.channel_bind_ids:
                        self.binder(rline_bind.external_id, rline_bind)

                processed_rids.append(rcode)
        return (processed_rids, any(failed_reservations),
                checkin_utc_dt, checkout_utc_dt)
