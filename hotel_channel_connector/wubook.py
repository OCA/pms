# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
import xmlrpc
import socket
import pytz
import json
from datetime import timedelta
from urllib.parse import urljoin
from odoo import models, api
from odoo.exceptions import UserError, ValidationError
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
from odoo.addons.payment.models.payment_acquirer import _partner_split_name
from odoo.addons.hotel import date_utils
_logger = logging.getLogger(__name__)

# GLOBAL VARS
DEFAULT_WUBOOK_DATE_FORMAT = "%d/%m/%Y"
DEFAULT_WUBOOK_TIME_FORMAT = "%H:%M"
DEFAULT_WUBOOK_DATETIME_FORMAT = "%s %s" % (DEFAULT_WUBOOK_DATE_FORMAT,
                                            DEFAULT_WUBOOK_TIME_FORMAT)
WUBOOK_STATUS_CONFIRMED = 1
WUBOOK_STATUS_WAITING = 2
WUBOOK_STATUS_REFUSED = 3
WUBOOK_STATUS_ACCEPTED = 4
WUBOOK_STATUS_CANCELLED = 5
WUBOOK_STATUS_CANCELLED_PENALTY = 6

WUBOOK_STATUS_GOOD = (
    WUBOOK_STATUS_CONFIRMED,
    WUBOOK_STATUS_WAITING,
    WUBOOK_STATUS_ACCEPTED,
)
WUBOOK_STATUS_BAD = (
    WUBOOK_STATUS_REFUSED,
    WUBOOK_STATUS_CANCELLED,
    WUBOOK_STATUS_CANCELLED_PENALTY,
)

# class TimeoutTransport(xmlrpclib.Transport):
#     """
#     Custom XML-RPC transport class for HTTP connections, allowing a timeout in
#     the base connection.
#     """
#
#     def __init__(self, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, use_datetime=0):
#         xmlrpclib.Transport.__init__(self, use_datetime)
#         self._timeout = timeout
#
#     def make_connection(self, host):
#         # If using python 2.6, since that implementation normally returns the
#         # HTTP compatibility class, which doesn't have a timeout feature.
#         #import httplib
#         #host, extra_headers, x509 = self.get_host_info(host)
#         #return httplib.HTTPConnection(host, timeout=self._timeout)
#
#         conn = xmlrpclib.Transport.make_connection(self, host)
#         conn.timeout = self._timeout
#         return conn


# WUBOOK
class WuBook(models.AbstractModel):
    _name = 'wubook'

    # === INITALIZATION
    def __init__(self, pool, cr):
        super(WuBook, self).__init__(pool, cr)
        self.SERVER = False
        self.LCODE = False
        self.TOKEN = False

    @api.model
    def initialize(self, activate):
        self_context = self.with_context({'init_connection': False})
        if not self_context.init_connection():
            return False
        if activate:
            if not self_context.push_activation():
                return False

        res = (self_context.import_rooms()[0]
               and self_context.import_channels_info()[0]
               and self_context.import_pricing_plans()[0]
               and self_context.import_restriction_plans()[0])

        self_context.close_connection()
        return res

    @api.model
    def push_activation(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        base_url = base_url.replace("http://", "https://")
        hotel_security_token = self.env['ir.default'].sudo().get(
            'wubook.config.settings', 'wubook_push_security_token')

        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode_a, results_a = self.SERVER.push_activation(
            self.TOKEN,
            self.LCODE,
            urljoin(base_url,
                    "/wubook/push/reservations/%s" % hotel_security_token),
            1)
        rcode_ua, results_ua = self.SERVER.push_update_activation(
            self.TOKEN,
            self.LCODE,
            urljoin(base_url, "/wubook/push/rooms/%s" % hotel_security_token))
        if init_connection:
            self.close_connection()

        if rcode_a != 0:
            self.create_wubook_issue('wubook',
                                     "Can't activate push reservations",
                                     results_a)
        if rcode_ua != 0:
            self.create_wubook_issue('wubook', "Can't activate push rooms",
                                     results_ua)

        return rcode_a == 0 and rcode_ua == 0

    def is_valid_account(self):
        user = self.env['ir.default'].sudo().get(
            'wubook.config.settings', 'wubook_user')
        passwd = self.env['ir.default'].sudo().get(
            'wubook.config.settings', 'wubook_passwd')
        lcode = self.env['ir.default'].sudo().get(
            'wubook.config.settings', 'wubook_lcode')
        pkey = self.env['ir.default'].sudo().get(
            'wubook.config.settings', 'wubook_pkey')
        server_addr = self.env['ir.default'].sudo().get(
            'wubook.config.settings', 'wubook_server')
        return bool(user and passwd and pkey and server_addr and lcode)

    # === NETWORK
    def init_connection(self):
        user = self.env['ir.default'].sudo().get(
            'wubook.config.settings', 'wubook_user')
        passwd = self.env['ir.default'].sudo().get(
            'wubook.config.settings', 'wubook_passwd')
        self.LCODE = self.env['ir.default'].sudo().get(
            'wubook.config.settings', 'wubook_lcode')
        pkey = self.env['ir.default'].sudo().get(
            'wubook.config.settings', 'wubook_pkey')
        server_addr = self.env['ir.default'].sudo().get(
            'wubook.config.settings', 'wubook_server')

        if not user or not passwd or not pkey or not server_addr or \
                not self.LCODE:
            self.create_wubook_issue(
                'wubook',
                "Can't connect with WuBook! Perhaps account not configured...",
                "")
            return False

        try:
            # t = TimeoutTransport(timeout=3)
            # self.SERVER = xmlrpclib.Server(server_addr, transport=t)
            self.SERVER = xmlrpclib.Server(server_addr)
            res, tok = self.SERVER.acquire_token(user, passwd, pkey)
            self.TOKEN = tok
            if res != 0:
                self.create_wubook_issue(
                    'wubook',
                    "Can't connect with WuBook! Perhaps the account haven't \
                        a good configuration...",
                    tok)
        except Exception:
            self.create_wubook_issue(
                'wubook',
                "Can't connect with WuBook! Please, check internet \
                    connection.",
                "")
            res = -1

        return res == 0

    def close_connection(self):
        self.SERVER.release_token(self.TOKEN)
        self.TOKEN = False
        self.SERVER = False

    # === HELPER FUNCTIONS
    @api.model
    def create_wubook_issue(self, section, message, wmessage, wid=False,
                            dfrom=False, dto=False):
        self.env['wubook.issue'].sudo().create({
            'section': section,
            'message': message,
            'wid': wid,
            'wmessage': wmessage,
            'date_start': dfrom and date_utils.get_datetime(
                dfrom,
                dtformat=DEFAULT_WUBOOK_DATE_FORMAT).strftime(
                    DEFAULT_SERVER_DATE_FORMAT),
            'date_end': dto and date_utils.get_datetime(
                dto,
                dtformat=DEFAULT_WUBOOK_DATE_FORMAT).strftime(
                    DEFAULT_SERVER_DATE_FORMAT),
        })

    def set_clousure_today(self, status):
        hotel_tz = self.env['ir.default'].sudo().get('hotel.config.settings',
                                                     'tz_hotel')
        now_utc_dt = date_utils.now()
        now_dt = date_utils.dt_as_timezone(now_utc_dt, hotel_tz)
        now_str = now_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
        vrooms = self.env['hotel.virtual.room'].search([])

        restriction_parity_id = self.env['ir.default'].sudo().get(
            'hotel.config.settings', 'parity_restrictions_id')
        if restriction_parity_id:
            restriction_parity_id = int(restriction_parity_id)

        vroom_restr_obj = self.env['hotel.virtual.room.restriction.item']
        vroom_obj = self.env['hotel.virtual.room']

        vrooms = vroom_obj.search([('wrid', '!=', False), ('wrid', '!=', '')])
        for vroom in vrooms:
            restr = vroom_restr_obj.search([
                ('restriction_id', '=', restriction_parity_id),
                ('virtual_room_id', '=', vroom.id),
                ('date_start', '>=', now_str),
                ('date_end', '<=', now_str),
                ('applied_on', '=', '0_virtual_room'),
            ], limit=1)
            if restr:
                restr.write({'closed': status})
            else:
                restr = vroom_restr_obj.create({
                    'date_start': now_str,
                    'date_end': now_str,
                    'virtual_room_id': vroom.id,
                    'applied_on': '0_virtual_room',
                    'restriction_id': restriction_parity_id,
                    'min_stay': 0,
                    'min_stay_arrival': 0,
                    'max_stay': 0,
                    'max_stay_arrival': 0,
                    'closed': status,
                    'closed_departure': False,
                    'closed_arrival': False,
                    'wpushed': False,
                })
                if not restr:
                    raise ValidationError("Can't close rooms!")
        return self.push_restrictions()

    # === ROOMS
    @api.model
    def create_room(self, shortcode, name, capacity, price, availability):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.new_room(
            self.TOKEN,
            self.LCODE,
            0,
            name,
            capacity,
            price,
            availability,
            shortcode[:4],
            'nb'    # TODO: Complete this part
            # rtype=('name' in vals and vals['name'] and 3) or 1
        )
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue(
                'room', "Can't create room in WuBook", results)
            return False

        return results

    @api.model
    def modify_room(self, wrid, name, capacity, price, availability, scode):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.mod_room(
            self.TOKEN,
            self.LCODE,
            wrid,
            name,
            capacity,
            price,
            availability,
            scode,
            'nb'
            # rtype=('name' in vals and vals['name'] and 3) or 1
        )
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('room', "Can't modify room in WuBook",
                                     results, wid=wrid)

        return rcode == 0

    @api.model
    def delete_room(self, wrid):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.del_room(
            self.TOKEN,
            self.LCODE,
            wrid
        )
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('room', "Can't delete room in WuBook",
                                     results, wid=wrid)

        return rcode == 0

    @api.model
    def import_rooms(self):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return (False, 0)
        rcode, results = self.SERVER.fetch_rooms(
            self.TOKEN,
            self.LCODE,
            0
        )
        if init_connection:
            self.close_connection()

        vroom_obj = self.env['hotel.virtual.room']
        count = 0
        if rcode == 0:
            count = len(results)
            for room in results:
                vroom = vroom_obj.search([('wrid', '=', room['id'])], limit=1)
                vals = {
                    'name': room['name'],
                    'wrid': room['id'],
                    'wscode': room['shortname'],
                    'list_price': room['price'],
                    'wcapacity': room['occupancy'],
                    # 'max_real_rooms': room['availability'],
                }
                if vroom:
                    vroom.with_context({'wubook_action': False}).write(vals)
                else:
                    vroom_obj.with_context({'wubook_action': False}).create(
                        vals)
        else:
            self.create_wubook_issue(
                'room', "Can't import rooms from WuBook", results)

        return (rcode == 0, count)

    @api.model
    def fetch_rooms_values(self, dfrom, dto, rooms=False,
                           set_wmax_avail=False):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        # Sanitize Dates
        now_dt = date_utils.now()
        now = now_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT)
        dfrom_dt = date_utils.get_datetime(dfrom,
                                           dtformat=DEFAULT_WUBOOK_DATE_FORMAT)
        dto_dt = date_utils.get_datetime(dto,
                                         dtformat=DEFAULT_WUBOOK_DATE_FORMAT)
        if dto_dt < now_dt:
            return True
        if dfrom_dt < now_dt:
            dfrom = now
        if dfrom_dt > dto_dt:
            dtemp = dfrom
            dfrom = dto
            dto = dtemp
        rcode, results = self.SERVER.fetch_rooms_values(self.TOKEN,
                                                        self.LCODE,
                                                        dfrom,
                                                        dto,
                                                        rooms)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('room',
                                     "Can't fetch rooms values from WuBook",
                                     results, dfrom=dfrom, dto=dto)
        else:
            self.generate_room_values(dfrom, dto, results,
                                      set_wmax_avail=set_wmax_avail)

        return rcode == 0

    @api.model
    def update_availability(self, rooms_avail):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.update_sparse_avail(self.TOKEN,
                                                         self.LCODE,
                                                         rooms_avail)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue(
                'room',
                "Can't update rooms availability in WuBook",
                results)

        return rcode == 0

    @api.model
    def corporate_fetch(self):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.corporate_fetchable_properties(self.TOKEN)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue(
                'wubook',
                "Can't call 'corporate_fetch' from WuBook",
                results)

        return rcode == 0

    # === RESERVATIONS
    @api.model
    def create_reservation(self, reserv):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        vroom = self.env['hotel.virtual.room'].search([
            ('product_id', '=', reserv.product_id.id)
        ], limit=1)
        customer = {
            'lname': _partner_split_name(reserv.partner_id.name)[0],
            'fname': _partner_split_name(reserv.partner_id.name)[1],
            'email': reserv.partner_id.email,
            'city': reserv.partner_id.city,
            'phone': reserv.partner_id.phone,
            'street': reserv.partner_id.street,
            'country': reserv.partner_id.country_id.code,
            'arrival_hour': date_utils.get_datetime(reserv.checkin,
                                                    dtformar="%H:%M:%S"),
            'notes': ''     # TODO:
        }
        rcode, results = self.SERVER.new_reservation(
            self.TOKEN,
            self.LCODE,
            reserv.checkin,
            reserv.checkout,
            {vroom.wrid: [reserv.adults+reserv.children, 'nb']},
            customer,
            reserv.adults+reserv.children)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('reservation',
                                     "Can't create reservations in wubook",
                                     results,
                                     dfrom=reserv.checkin, dto=reserv.checkout)
        else:
            reserv.write({'wrid': results})

        return rcode == 0

    @api.model
    def cancel_reservation(self, wrid, reason=""):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.cancel_reservation(self.TOKEN,
                                                        self.LCODE,
                                                        wrid,
                                                        reason)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('reservation',
                                     "Can't cancel reservation in WuBook",
                                     results, wid=wrid)

        return rcode == 0

    @api.model
    def fetch_new_bookings(self):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return (False, 0)
        rcode, results = self.SERVER.fetch_new_bookings(self.TOKEN,
                                                        self.LCODE,
                                                        1,
                                                        0)
        errors = False
        processed_rids = []
        if rcode == 0:
            processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
                self.generate_reservations(results)
            if any(processed_rids):
                uniq_rids = list(set(processed_rids))
                rcodeb, resultsb = self.SERVER.mark_bookings(self.TOKEN,
                                                             self.LCODE,
                                                             uniq_rids)

                if rcodeb != 0:
                    self.create_wubook_issue(
                        'wubook',
                        "Problem trying mark bookings (%s)" %
                        str(processed_rids),
                        '')
        if init_connection:
            self.close_connection()

        # Update Odoo availability (don't wait for wubook)
        if rcode == 0 and checkin_utc_dt and checkout_utc_dt:
            self.fetch_rooms_values(
                checkin_utc_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                checkout_utc_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT))

        if rcode != 0:
            self.create_wubook_issue('reservation',
                                     "Can't process reservations from wubook",
                                     results)

        return ((rcode == 0 and not errors), len(processed_rids))

    @api.model
    def fetch_booking(self, lcode, wrid):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return (False, 0)
        rcode, results = self.SERVER.fetch_booking(self.TOKEN,
                                                   lcode,
                                                   wrid)
        errors = False
        processed_rids = []
        if rcode == 0:
            processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
                self.generate_reservations(results)
            if any(processed_rids):
                uniq_rids = list(set(processed_rids))
                rcode, results = self.SERVER.mark_bookings(self.TOKEN,
                                                           self.LCODE,
                                                           uniq_rids)

                if rcode != 0:
                    self.create_wubook_issue(
                        'wubook',
                        "Problem trying mark bookings (%s)" %
                        str(processed_rids),
                        '')

        if init_connection:
            self.close_connection()

        # Update Odoo availability (don't wait for wubook)
        if rcode == 0 and checkin_utc_dt and checkout_utc_dt:
            self.fetch_rooms_values(
                checkin_utc_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                checkout_utc_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT))

        if rcode != 0:
            self.create_wubook_issue('reservation',
                                     "Can't process reservations from wubook",
                                     results, wid=wrid)

        return ((rcode == 0 and not errors), len(processed_rids))

    @api.model
    def mark_bookings(self, wrids):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.mark_bookings(self.TOKEN,
                                                   self.LCODE,
                                                   wrids)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue(
                'reservation',
                "Can't mark as readed a reservation in wubook",
                results, wid=str(wrids))

        return rcode == 0

    # === PRICE PLANS
    @api.model
    def create_plan(self, name, daily=1):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.add_pricing_plan(self.TOKEN,
                                                      self.LCODE,
                                                      name,
                                                      daily)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue(
                'plan', "Can't add pricing plan to wubook", results)
            return False

        return results

    @api.model
    def delete_plan(self, pid):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.del_plan(self.TOKEN,
                                              self.LCODE,
                                              pid)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('plan',
                                     "Can't delete pricing plan from wubook",
                                     results,
                                     wid=pid)

        return rcode == 0

    @api.model
    def update_plan_name(self, pid, name):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.update_plan_name(self.TOKEN,
                                                      self.LCODE,
                                                      pid,
                                                      name)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue(
                'plan',
                "Can't update pricing plan name in wubook",
                results, wid=pid)

        return rcode == 0

    @api.model
    def update_plan_prices(self, pid, dfrom, prices):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.update_plan_prices(self.TOKEN,
                                                        self.LCODE,
                                                        pid,
                                                        dfrom,
                                                        prices)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue(
                'plan',
                "Can't update pricing plan in wubook",
                results, wid=pid, dfrom=dfrom)

        return rcode == 0

    @api.model
    def update_plan_periods(self, pid, periods):
        _logger.info("[WuBook] Updating Plan Periods...")
        _logger.info(periods)
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.update_plan_periods(self.TOKEN,
                                                         self.LCODE,
                                                         pid,
                                                         periods)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue(
                'plan',
                "Can't update pricing plan period in wubook",
                results, wid=pid)

        return rcode == 0

    @api.model
    def import_pricing_plans(self):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return (False, 0)
        rcode, results = self.SERVER.get_pricing_plans(self.TOKEN,
                                                       self.LCODE)
        if init_connection:
            self.close_connection()

        count = 0
        if rcode != 0:
            self.create_wubook_issue(
                'plan',
                "Can't get pricing plans from wubook",
                results)
        else:
            count = self.generate_pricelists(results)

        return (rcode == 0, count)

    @api.model
    def fetch_plan_prices(self, pid, dfrom, dto, rooms=None):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.fetch_plan_prices(self.TOKEN,
                                                       self.LCODE,
                                                       pid,
                                                       dfrom,
                                                       dto,
                                                       rooms or [])
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue(
                'plan',
                "Can't fetch plan prices from wubook",
                results, wid=pid, dfrom=dfrom, dto=dto)
        else:
            self.generate_pricelist_items(pid, dfrom, dto, results)

        return rcode == 0

    @api.model
    def fetch_all_plan_prices(self, dfrom, dto, rooms=None):
        no_errors = True
        plan_wpids = self.env['product.pricelist'].search([
            ('wpid', '!=', False), ('wpid', '!=', '')
        ]).mapped('wpid')
        if any(plan_wpids):
            init_connection = self._context.get('init_connection', True)
            if init_connection:
                if not self.init_connection():
                    return False
            for wpid in plan_wpids:
                rcode, results = self.SERVER.fetch_plan_prices(self.TOKEN,
                                                               self.LCODE,
                                                               wpid,
                                                               dfrom,
                                                               dto,
                                                               rooms or [])
                if rcode != 0:
                    self.create_wubook_issue(
                        'plan',
                        "Can't fetch all plan prices from wubook!",
                        results, wid=wpid, dfrom=dfrom, dto=dto)
                    no_errors = False
                else:
                    self.generate_pricelist_items(wpid, dfrom, dto, results)
            if init_connection:
                self.close_connection()

        return no_errors

    # === RESTRICTION PLANS
    @api.model
    def import_restriction_plans(self):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return (False, 0)
        rcode, results = self.SERVER.rplan_rplans(self.TOKEN,
                                                  self.LCODE)
        if init_connection:
            self.close_connection()

        count = 0
        if rcode != 0:
            self.create_wubook_issue(
                'rplan',
                "Can't fetch restriction plans from wubook",
                results)
        else:
            count = self.generate_restrictions(results)

        return (rcode == 0, count)

    @api.model
    def fetch_rplan_restrictions(self, dfrom, dto, rpid=False):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.wired_rplan_get_rplan_values(self.TOKEN,
                                                                  self.LCODE,
                                                                  dfrom,
                                                                  dto,
                                                                  int(rpid))
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue(
                'rplan',
                "Can't fetch plan restrictions from wubook",
                results, wid=rpid, dfrom=dfrom, dto=dto)
        elif any(results):
            self.generate_restriction_items(dfrom, dto, results)

        return rcode == 0

    @api.model
    def update_rplan_values(self, rpid, dfrom, values):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.rplan_update_rplan_values(self.TOKEN,
                                                               self.LCODE,
                                                               rpid,
                                                               dfrom,
                                                               values)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue(
                'rplan',
                "Can't update plan restrictions on wubook",
                results, wid=rpid, dfrom=dfrom)

        return rcode == 0

    @api.model
    def create_rplan(self, name, compact=False):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.rplan_add_rplan(self.TOKEN,
                                                     self.LCODE,
                                                     name,
                                                     compact and 1 or 0)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('rplan',
                                     "Can't create plan restriction in wubook",
                                     results)
            return False

        return results

    @api.model
    def rename_rplan(self, rpid, name):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.rplan_rename_rplan(self.TOKEN,
                                                        self.LCODE,
                                                        rpid,
                                                        name)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('rplan',
                                     "Can't rename plan restriction in wubook",
                                     results, wid=rpid)

        return rcode == 0

    @api.model
    def delete_rplan(self, rpid):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self.SERVER.rplan_del_rplan(self.TOKEN,
                                                     self.LCODE,
                                                     rpid)
        if init_connection:
            self.close_connection()

        if rcode != 0:
            self.create_wubook_issue('rplan',
                                     "Can't delete plan restriction on wubook",
                                     results, wid=rpid)

        return rcode == 0

    # === WUBOOK INFO
    @api.model
    def import_channels_info(self):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return (False, 0)
        results = self.SERVER.get_channels_info(self.TOKEN)
        if init_connection:
            self.close_connection()

        count = self.generate_wubook_channel_info(results)

        return (True, count)

    # === WUBOOK -> ODOO
    @api.model
    def generate_room_values(self, dfrom, dto, values, set_wmax_avail=False):
        virtual_room_avail_obj = self.env['hotel.virtual.room.availability']
        virtual_room_restr_obj = self.env['hotel.virtual.room.restriction']
        vroom_restr_item_obj = self.env['hotel.virtual.room.restriction.item']
        hotel_virtual_room_obj = self.env['hotel.virtual.room']
        def_wubook_restr = virtual_room_restr_obj.search([('wpid', '=', '0')])
        _logger.info("==== ROOM VALUES (%s -- %s)", dfrom, dto)
        _logger.info(values)
        for k_rid, v_rid in values.iteritems():
            vroom = hotel_virtual_room_obj.search([
                ('wrid', '=', k_rid)
            ], limit=1)
            if vroom:
                date_dt = date_utils.get_datetime(
                    dfrom,
                    dtformat=DEFAULT_WUBOOK_DATE_FORMAT)
                for day_vals in v_rid:
                    date_str = date_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    # Get Availability
                    vroom_avail = virtual_room_avail_obj.search([
                        ('virtual_room_id', '=', vroom.id),
                        ('date', '=', date_str)
                    ], limit=1)
                    vals = {
                        'no_ota': day_vals.get('no_ota'),
                        'booked': day_vals.get('booked'),
                        'avail': day_vals.get('avail', 0),
                        'wpushed': True,
                    }
                    if set_wmax_avail:
                        vals.update({'wmax_avail': day_vals.get('avail', 0)})
                    if vroom_avail:
                        vroom_avail.with_context({
                            'wubook_action': False,
                        }).write(vals)
                    else:
                        vals.update({
                            'virtual_room_id': vroom.id,
                            'date': date_str,
                        })
                        virtual_room_avail_obj.with_context({
                            'wubook_action': False,
                            'mail_create_nosubscribe': True,
                        }).create(vals)

                    # Get Restrictions
                    if def_wubook_restr:
                        vroom_restr = vroom_restr_item_obj.search([
                            ('virtual_room_id', '=', vroom.id),
                            ('applied_on', '=', '0_virtual_room'),
                            ('date_start', '=', date_str),
                            ('date_end', '=', date_str),
                            ('restriction_id', '=', def_wubook_restr.id),
                        ])
                        vals = {
                            'min_stay': int(day_vals.get('min_stay', 0)),
                            'min_stay_arrival': int(day_vals.get(
                                'min_stay_arrival',
                                0)),
                            'max_stay': int(day_vals.get('max_stay', 0)),
                            'max_stay_arrival': int(day_vals.get(
                                'max_stay_arrival',
                                0)),
                            'closed': int(day_vals.get('closed', False)),
                            'closed_departure': int(day_vals.get(
                                'closed_departure',
                                False)),
                            'closed_arrival': int(day_vals.get(
                                'closed_arrival',
                                False)),
                            'wpushed': True,
                        }
                        if vroom_restr:
                            vroom_restr.with_context({
                                'wubook_action': False,
                            }).write(vals)
                        else:
                            vals.update({
                                'restriction_id': def_wubook_restr.id,
                                'virtual_room_id': vroom.id,
                                'date_start': date_str,
                                'date_end': date_str,
                                'applied_on': '0_virtual_room',
                            })
                            vroom_restr_item_obj.with_context({
                                'wubook_action': False,
                            }).create(vals)
                    date_dt = date_dt + timedelta(days=1)
        return True

    @api.model
    def generate_restrictions(self, restriction_plans):
        restriction_obj = self.env['hotel.virtual.room.restriction']
        count = 0
        for plan in restriction_plans:
            vals = {
                'name': plan['name'],
            }
            plan_id = restriction_obj.search([
                ('wpid', '=', str(plan['id']))
            ], limit=1)
            if not plan_id:
                vals.update({
                    'wpid': str(plan['id']),
                })
                restriction_obj.with_context({
                    'wubook_action': False,
                    'rules': plan.get('rules'),
                }).create(vals)
            else:
                plan_id.with_context({'wubook_action': False}).write(vals)
            count = count + 1
        return count

    @api.model
    def generate_restriction_items(self, dfrom, dto, plan_restrictions):
        hotel_virtual_room_obj = self.env['hotel.virtual.room']
        reserv_restriction_obj = self.env['hotel.virtual.room.restriction']
        restriction_item_obj = self.env['hotel.virtual.room.restriction.item']
        _logger.info("===== RESTRICTIONS")
        _logger.info(plan_restrictions)
        for k_rpid, v_rpid in plan_restrictions.iteritems():
            restriction_id = reserv_restriction_obj.search([
                ('wpid', '=', k_rpid)
            ], limit=1)
            if restriction_id:
                for k_rid, v_rid in v_rpid.iteritems():
                    vroom = hotel_virtual_room_obj.search([
                        ('wrid', '=', k_rid)
                    ], limit=1)
                    if vroom:
                        for item in v_rid:
                            date_dt = date_utils.get_datetime(
                                item['date'],
                                dtformat=DEFAULT_WUBOOK_DATE_FORMAT)
                            restriction_item = restriction_item_obj.search([
                                ('restriction_id', '=', restriction_id.id),
                                ('date_start', '=', date_dt.strftime(
                                    DEFAULT_SERVER_DATE_FORMAT)),
                                ('date_end', '=', date_dt.strftime(
                                    DEFAULT_SERVER_DATE_FORMAT)),
                                ('applied_on', '=', '0_virtual_room'),
                                ('virtual_room_id', '=', vroom.id)
                            ], limit=1)
                            vals = {
                                'closed_arrival': item['closed_arrival'],
                                'closed': item['closed'],
                                'min_stay': item['min_stay'],
                                'closed_departure': item['closed_departure'],
                                'max_stay': item['max_stay'],
                                'max_stay_arrival': item['max_stay_arrival'],
                                'min_stay_arrival': item['min_stay_arrival'],
                                'wpushed': True,
                            }
                            if restriction_item:
                                restriction_item.with_context({
                                    'wubook_action': False}).write(vals)
                            else:
                                vals.update({
                                    'restriction_id': restriction_id.id,
                                    'date_start': date_dt.strftime(
                                        DEFAULT_SERVER_DATE_FORMAT),
                                    'date_end': date_dt.strftime(
                                        DEFAULT_SERVER_DATE_FORMAT),
                                    'applied_on': '0_virtual_room',
                                    'virtual_room_id': vroom.id
                                })
                                restriction_item_obj.with_context({
                                    'wubook_action': False}).create(vals)

        return True

    @api.model
    def generate_pricelist_items(self, pid, dfrom, dto, plan_prices):
        hotel_virtual_room_obj = self.env['hotel.virtual.room']
        pricelist = self.env['product.pricelist'].search([
            ('wpid', '=', pid)
        ], limit=1)
        if pricelist:
            pricelist_item_obj = self.env['product.pricelist.item']
            dfrom_dt = date_utils.get_datetime(
                dfrom,
                dtformat=DEFAULT_WUBOOK_DATE_FORMAT)
            dto_dt = date_utils.get_datetime(
                dto,
                dtformat=DEFAULT_WUBOOK_DATE_FORMAT)
            days_diff = date_utils.date_diff(dfrom_dt, dto_dt, hours=False) + 1
            for i in range(0, days_diff):
                ndate_dt = dfrom_dt + timedelta(days=i)
                for k_rid, v_rid in plan_prices.iteritems():
                    vroom = hotel_virtual_room_obj.search([
                        ('wrid', '=', k_rid)
                    ], limit=1)
                    if vroom:
                        pricelist_item = pricelist_item_obj.search([
                            ('pricelist_id', '=', pricelist.id),
                            ('date_start', '=', ndate_dt.strftime(
                                DEFAULT_SERVER_DATE_FORMAT)),
                            ('date_end', '=', ndate_dt.strftime(
                                DEFAULT_SERVER_DATE_FORMAT)),
                            ('compute_price', '=', 'fixed'),
                            ('applied_on', '=', '1_product'),
                            ('product_tmpl_id', '=', vroom.product_id.product_tmpl_id.id)
                        ], limit=1)
                        vals = {
                            'fixed_price': plan_prices[k_rid][i],
                            'wpushed': True,
                        }
                        if pricelist_item:
                            pricelist_item.with_context({
                                'wubook_action': False}).write(vals)
                        else:
                            vals.update({
                                'pricelist_id': pricelist.id,
                                'date_start': ndate_dt.strftime(
                                    DEFAULT_SERVER_DATE_FORMAT),
                                'date_end': ndate_dt.strftime(
                                    DEFAULT_SERVER_DATE_FORMAT),
                                'compute_price': 'fixed',
                                'applied_on': '1_product',
                                'product_tmpl_id': vroom.product_id.product_tmpl_id.id
                            })
                            pricelist_item_obj.with_context({
                                'wubook_action': False}).create(vals)
        return True

    @api.model
    def generate_pricelists(self, price_plans):
        product_listprice_obj = self.env['product.pricelist']
        count = 0
        for plan in price_plans:
            if 'vpid' in plan:
                continue    # Ignore Virtual Plans

            vals = {
                'name': plan['name'],
                'wdaily': plan['daily'] == 1,
            }
            plan_id = product_listprice_obj.search([
                ('wpid', '=', str(plan['id']))
            ], limit=1)
            if not plan_id:
                vals.update({
                    'wpid': str(plan['id']),
                })
                product_listprice_obj.with_context({
                    'wubook_action': False}).create(vals)
            else:
                plan_id.with_context({'wubook_action': False}).write(vals)
            count = count + 1
        return count

    @api.model
    def _generate_booking_vals(self, broom, checkin_str, checkout_str,
                               is_cancellation, wchannel_info, wstatus, crcode,
                               rcode, vroom, split_booking, dates_checkin,
                               dates_checkout, book):
        # Generate Reservation Day Lines
        reservation_line_ids = []
        tprice = 0.0
        for brday in broom['roomdays']:
            wndate = date_utils.get_datetime(
                brday['day'],
                dtformat=DEFAULT_WUBOOK_DATE_FORMAT
            ).replace(tzinfo=pytz.utc)
            if date_utils.date_in(wndate,
                                  dates_checkin[0],
                                  dates_checkout[0] - timedelta(days=1),
                                  hours=False) == 0:
                reservation_line_ids.append((0, False, {
                    'date': wndate.strftime(
                        DEFAULT_SERVER_DATE_FORMAT),
                    'price': brday['price']
                }))
                tprice += brday['price']
        persons = vroom.wcapacity
        if 'ancillary' in broom and 'guests' in broom['ancillary']:
            persons = broom['ancillary']['guests']
        vals = {
            'checkin': checkin_str,
            'checkout': checkout_str,
            'adults': persons,
            'children': book['children'],
            'reservation_line_ids': reservation_line_ids,
            'price_unit': tprice,
            'to_assign': True,
            'wrid': rcode,
            'wchannel_id': wchannel_info and wchannel_info.id,
            'wchannel_reservation_code': crcode,
            'wstatus': wstatus,
            'to_read': True,
            'state': is_cancellation and 'cancelled' or 'draft',
            'virtual_room_id': vroom.id,
            'splitted': split_booking,
            'wbook_json': json.dumps(book),
            'wmodified': book['was_modified']
        }
        _logger.info("===== CONTRUCT RESERV")
        _logger.info(vals)
        return vals

    @api.model
    def _generate_partner_vals(self, book):
        country_id = self.env['res.country'].search([
            ('code', '=', str(book['customer_country']))
        ], limit=1)
        # lang = self.env['res.lang'].search([('code', '=', book['customer_language_iso'])], limit=1)
        return {
            'name': "%s, %s" %
                    (book['customer_surname'], book['customer_name']),
            'country_id': country_id and country_id.id,
            'city': book['customer_city'],
            'phone': book['customer_phone'],
            'zip': book['customer_zip'],
            'street': book['customer_address'],
            'email': book['customer_mail'],
            'unconfirmed': True,
            # 'lang': lang and lang.id,
        }

    # FIXME: Super big method!!! O_o
    @api.model
    def generate_reservations(self, bookings):
        _logger.info("=== BOOKINGS FROM WUBOOK")
        _logger.info(bookings)
        default_arrival_hour = self.env['ir.default'].sudo().get(
            'hotel.config.settings', 'default_arrival_hour')
        default_departure_hour = self.env['ir.default'].sudo().get(
            'hotel.config.settings', 'default_departure_hour')

        # Get user timezone
        tz_hotel = self.env['ir.default'].sudo().get(
            'hotel.config.settings', 'tz_hotel')
        res_partner_obj = self.env['res.partner']
        hotel_reserv_obj = self.env['hotel.reservation']
        hotel_folio_obj = self.env['hotel.folio']
        hotel_vroom_obj = self.env['hotel.virtual.room']
        # Space for store some data for construct folios
        processed_rids = []
        failed_reservations = []
        checkin_utc_dt = False
        checkout_utc_dt = False
        split_booking = False
        for book in bookings:   # This create a new folio
            splitted_map = {}
            is_cancellation = book['status'] in WUBOOK_STATUS_BAD
            bstatus = str(book['status'])
            rcode = str(book['reservation_code'])
            crcode = str(book['channel_reservation_code']) \
                if book['channel_reservation_code'] else 'undefined'

            # Can't process failed reservations
            #  (for example set a invalid new reservation and receive in
            # the same transaction an cancellation)
            if crcode in failed_reservations:
                self.create_wubook_issue(
                    'reservation',
                    "Can't process a reservation that previusly failed!",
                    '', wid=book['reservation_code'])
                continue

            # Get dates for the reservation (GMT->UTC)
            arr_hour = default_arrival_hour if book['arrival_hour'] == "--" \
                else book['arrival_hour']
            checkin = "%s %s" % (book['date_arrival'], arr_hour)
            checkin_dt = date_utils.get_datetime(
                checkin,
                dtformat=DEFAULT_WUBOOK_DATETIME_FORMAT,
                stz=tz_hotel)
            checkin_utc_dt = date_utils.dt_as_timezone(checkin_dt, 'UTC')
            checkin = checkin_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            checkout = "%s %s" % (book['date_departure'],
                                  default_departure_hour)
            checkout_dt = date_utils.get_datetime(
                checkout,
                dtformat=DEFAULT_WUBOOK_DATETIME_FORMAT,
                stz=tz_hotel)
            checkout_utc_dt = date_utils.dt_as_timezone(checkout_dt, 'UTC')
            checkout = checkout_utc_dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            # Search Folio. If exists.
            folio_id = False
            if crcode != 'undefined':
                reserv_folio = hotel_reserv_obj.search([
                    ('wchannel_reservation_code', '=', crcode)
                ], limit=1)
                if reserv_folio:
                    folio_id = reserv_folio.folio_id
            else:
                reserv_folio = hotel_reserv_obj.search([
                    ('wrid', '=', rcode)
                ], limit=1)
                if reserv_folio:
                    folio_id = reserv_folio.folio_id

            # Need update reservations?
            sreservs = hotel_reserv_obj.search([('wrid', '=', rcode)])
            reservs = folio_id.room_lines if folio_id else sreservs
            reservs_processed = False
            if any(reservs):
                folio_id = reservs[0].folio_id
                for reserv in reservs:
                    if reserv.wrid == rcode:
                        reserv.with_context({'wubook_action': False}).write({
                            'wstatus': str(book['status']),
                            'wstatus_reason': book.get('status_reason', ''),
                            'to_read': True,
                            'to_assign': True,
                            'price_unit': book['amount'],
                            'wcustomer_notes': book['customer_notes'],
                            'wbook_json': json.dumps(book),
                        })
                        if reserv.partner_id.unconfirmed:
                            reserv.partner_id.write(
                                self._generate_partner_vals(book)
                            )
                        reservs_processed = True
                        if is_cancellation:
                            reserv.with_context({
                                'wubook_action': False}).action_cancel()
                        elif reserv.state == 'cancelled':
                            reserv.with_context({
                                'wubook_action': False,
                            }).write({
                                'discount': 0.0,
                                'state': 'confirm',
                            })

            # Do Nothing if already processed 'wrid'
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

            # Search Wubook Channel Info
            wchannel_info = self.env['wubook.channel.info'].search(
                [('wid', '=', str(book['id_channel']))], limit=1)

            reservations = []
            used_rooms = []
            # Iterate booked rooms
            for broom in book['booked_rooms']:
                vroom = hotel_vroom_obj.search([
                    ('wrid', '=', broom['room_id'])
                ], limit=1)
                if not vroom:
                    self.create_wubook_issue(
                        'reservation',
                        "Can't found any virtual room associated to '%s' \
                                                in this hotel" % book['rooms'],
                        '', wid=book['reservation_code'])
                    failed_reservations.append(crcode)
                    continue

                dates_checkin = [checkin_utc_dt, False]
                dates_checkout = [checkout_utc_dt, False]
                split_booking = False
                split_booking_parent = False
                # This perhaps create splitted reservation
                while dates_checkin[0]:
                    checkin_str = dates_checkin[0].strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT)
                    checkout_str = dates_checkout[0].strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT)
                    vals = self._generate_booking_vals(
                        broom,
                        checkin_str,
                        checkout_str,
                        is_cancellation,
                        wchannel_info,
                        bstatus,
                        crcode,
                        rcode,
                        vroom,
                        split_booking,
                        dates_checkin,
                        dates_checkout,
                        book,
                    )
                    if vals['price_unit'] != book['amount']:
                        self.create_wubook_issue(
                            'reservation',
                            "Invalid reservation total price! %.2f != %.2f" % (vals['price_unit'], book['amount']),
                            '', wid=book['reservation_code'])

                    free_rooms = hotel_vroom_obj.check_availability_virtual_room(
                        checkin_str,
                        checkout_str,
                        virtual_room_id=vroom.id,
                        notthis=used_rooms)
                    if any(free_rooms):
                        vals.update({
                            'product_id': free_rooms[0].product_id.id,
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
                            # Can't found space for reservation
                            vals = self._generate_booking_vals(
                                broom,
                                checkin_utc_dt,
                                checkout_utc_dt,
                                is_cancellation,
                                wchannel_info,
                                bstatus,
                                crcode,
                                rcode,
                                vroom,
                                False,
                                (checkin_utc_dt, False),
                                (checkout_utc_dt, False),
                                book,
                            )
                            vals.update({
                                'product_id':
                                    vroom.room_ids[0].product_id.id,
                                'name': vroom.name,
                                'overbooking': True,
                            })
                            reservations.append((0, False, vals))
                            self.create_wubook_issue(
                                'reservation',
                                "Reservation imported with overbooking state",
                                '', wid=rcode)
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

            if split_booking:
                self.create_wubook_issue(
                    'reservation',
                    "Reservation Splitted",
                    '', wid=rcode)

            # Create Folio
            if not any(failed_reservations) and any(reservations):
                try:
                    # TODO: Improve 'addons_list' & discounts
                    addons = str(book['addons_list']) if any(book['addons_list']) else ''
                    discounts = book.get('discount', '')
                    vals = {
                        'room_lines': reservations,
                        'wcustomer_notes': "%s\nADDONS:\n%s\nDISCOUNT:\n%s" % (
                            book['customer_notes'], addons, discounts),
                        'channel_type': 'web',
                    }
                    _logger.info("=== FOLIO CREATE")
                    _logger.info(reservations)
                    if folio_id:
                        folio_id.with_context({
                            'wubook_action': False}).write(vals)
                    else:
                        vals.update({
                            'partner_id': partner_id.id,
                            'wseed': book['sessionSeed']
                        })
                        folio_id = hotel_folio_obj.with_context({
                            'wubook_action': False}).create(vals)

                    # Update Reservation Spitted Parents
                    sorted_rlines = folio_id.room_lines.sorted(key='id')
                    for k_pid, v_pid in splitted_map.iteritems():
                        preserv = sorted_rlines[k_pid-1]
                        for pid in v_pid:
                            creserv = sorted_rlines[pid-1]
                            creserv.parent_reservation = preserv.id

                    processed_rids.append(rcode)
                except Exception as e_msg:
                    self.create_wubook_issue(
                        'reservation',
                        e_msg[0],
                        '', wid=rcode)
                    failed_reservations.append(crcode)
        return (processed_rids, any(failed_reservations),
                checkin_utc_dt, checkout_utc_dt)

    @api.model
    def generate_wubook_channel_info(self, channels):
        channel_info_obj = self.env['wubook.channel.info']
        count = 0
        for k_cid, v_cid in channels.iteritems():
            vals = {
                'name': v_cid['name'],
                'ical': v_cid['ical'] == 1,
            }
            channel_info = channel_info_obj.search([
                ('wid', '=', k_cid)
            ], limit=1)
            if channel_info:
                channel_info.write(vals)
            else:
                vals.update({
                    'wid': k_cid
                })
                channel_info_obj.create(vals)
            count = count + 1
        return count

    # === ODOO -> WUBOOK
    @api.model
    def push_changes(self):
        return self.push_availability() and self.push_priceplans() and \
                self.push_restrictions()

    @api.model
    def push_availability(self):
        vroom_avail_ids = self.env['hotel.virtual.room.availability'].search([
            ('wpushed', '=', False),
            ('date', '>=', date_utils.now(hours=False).strftime(
                DEFAULT_SERVER_DATE_FORMAT))
        ])

        vrooms = vroom_avail_ids.mapped('virtual_room_id')
        avails = []
        for vroom in vrooms:
            vroom_avails = vroom_avail_ids.filtered(
                lambda x: x.virtual_room_id.id == vroom.id)
            days = []
            for vroom_avail in vroom_avails:
                vroom_avail.with_context({
                    'wubook_action': False}).write({'wpushed': True})
                wavail = vroom_avail.avail
                if wavail > vroom_avail.wmax_avail:
                    wavail = vroom_avail.wmax_avail
                date_dt = date_utils.get_datetime(
                    vroom_avail.date,
                    dtformat=DEFAULT_SERVER_DATE_FORMAT)
                days.append({
                    'date': date_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                    'avail': wavail,
                    'no_ota': vroom_avail.no_ota and 1 or 0,
                    # 'booked': vroom_avail.booked and 1 or 0,
                })
            avails.append({'id': vroom.wrid, 'days': days})
        _logger.info("UPDATING AVAILABILITY IN WUBOOK...")
        _logger.info(avails)
        if any(avails):
            self.update_availability(avails)
        return True

    @api.model
    def push_priceplans(self):
        unpushed = self.env['product.pricelist.item'].search([
            ('wpushed', '=', False),
            ('date_start', '>=', date_utils.now(hours=False).strftime(
                DEFAULT_SERVER_DATE_FORMAT))
        ], order="date_start ASC")
        if any(unpushed):
            date_start = date_utils.get_datetime(
                unpushed[0].date_start,
                dtformat=DEFAULT_SERVER_DATE_FORMAT)
            date_end = date_utils.get_datetime(
                unpushed[-1].date_start,
                dtformat=DEFAULT_SERVER_DATE_FORMAT)
            days_diff = date_utils.date_diff(date_start, date_end, hours=False) + 1

            prices = {}
            pricelist_ids = self.env['product.pricelist'].search([
                ('wpid', '!=', False),
                ('active', '=', True)
            ])
            for pr in pricelist_ids:
                prices.update({pr.wpid: {}})
                unpushed_pl = self.env['product.pricelist.item'].search(
                    [('wpushed', '=', False), ('pricelist_id', '=', pr.id)])
                product_tmpl_ids = unpushed_pl.mapped('product_tmpl_id')
                for pt_id in product_tmpl_ids:
                    vroom = self.env['hotel.virtual.room'].search([
                        ('product_id.product_tmpl_id', '=', pt_id.id)
                    ], limit=1)
                    if vroom:
                        prices[pr.wpid].update({vroom.wrid: []})
                        for i in range(0, days_diff):
                            prod = vroom.product_id.with_context({
                                'quantity': 1,
                                'pricelist': pr.id,
                                'date': (date_start + timedelta(days=i)).
                                        strftime(DEFAULT_SERVER_DATE_FORMAT),
                                })
                            prices[pr.wpid][vroom.wrid].append(prod.price)
            _logger.info("UPDATING PRICES IN WUBOOK...")
            _logger.info(prices)
            for k_pk, v_pk in prices.iteritems():
                if any(v_pk):
                    self.update_plan_prices(k_pk, date_start.strftime(
                        DEFAULT_WUBOOK_DATE_FORMAT), v_pk)

            unpushed.with_context({
                'wubook_action': False}).write({'wpushed': True})
        return True

    @api.model
    def push_restrictions(self):
        vroom_rest_obj = self.env['hotel.virtual.room.restriction']
        rest_item_obj = self.env['hotel.virtual.room.restriction.item']
        unpushed = rest_item_obj.search([
            ('wpushed', '=', False),
            ('date_start', '>=', date_utils.now(hours=False).strftime(
                DEFAULT_SERVER_DATE_FORMAT))
        ], order="date_start ASC")
        if any(unpushed):
            date_start = date_utils.get_datetime(
                unpushed[0].date_start,
                dtformat=DEFAULT_SERVER_DATE_FORMAT)
            date_end = date_utils.get_datetime(
                unpushed[-1].date_start,
                dtformat=DEFAULT_SERVER_DATE_FORMAT)
            days_diff = date_utils.date_diff(
                date_start,
                date_end,
                hours=False) + 1
            restrictions = {}
            restriction_plan_ids = vroom_rest_obj.search([
                ('wpid', '!=', False),
                ('active', '=', True)
            ])
            for rp in restriction_plan_ids:
                restrictions.update({rp.wpid: {}})
                unpushed_rp = rest_item_obj.search([
                    ('wpushed', '=', False),
                    ('restriction_id', '=', rp.id)
                ])
                virtual_room_ids = unpushed_rp.mapped('virtual_room_id')
                for vroom in virtual_room_ids:
                    restrictions[rp.wpid].update({vroom.wrid: []})
                    for i in range(0, days_diff):
                        ndate_dt = date_start + timedelta(days=i)
                        restr = vroom.get_restrictions(
                            ndate_dt.strftime(DEFAULT_SERVER_DATE_FORMAT))
                        if restr:
                            restrictions[rp.wpid][vroom.wrid].append({
                                'min_stay': restr.min_stay or 0,
                                'min_stay_arrival': restr.min_stay_arrival or 0,
                                'max_stay': restr.max_stay or 0,
                                'max_stay_arrival': restr.max_stay_arrival or 0,
                                'closed': restr.closed and 1 or 0,
                                'closed_arrival': restr.closed_arrival and 1 or 0,
                                'closed_departure': restr.closed_departure and 1 or 0,
                            })
                        else:
                            restrictions[rp.wpid][vroom.wrid].append({})
            _logger.info("UPDATING RESTRICTIONS IN WUBOOK...")
            _logger.info(restrictions)
            for k_res, v_res in restrictions.iteritems():
                if any(v_res):
                    self.update_rplan_values(
                        int(k_res),
                        date_start.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                        v_res)
            unpushed.with_context({
                'wubook_action': False}).write({'wpushed': True})
        return True
