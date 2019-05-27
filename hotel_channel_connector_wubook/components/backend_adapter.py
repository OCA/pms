# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta
import xmlrpc.client
from urllib.parse import urljoin
from odoo.addons.component.core import AbstractComponent
from odoo.addons.queue_job.exception import RetryableJobError
from odoo.addons.payment.models.payment_acquirer import _partner_split_name
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo import fields, _
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

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


class WuBookLogin(object):
    def __init__(self, address, user, passwd, lcode, pkey):
        self.address = address
        self.user = user
        self.passwd = passwd
        self.lcode = lcode
        self.pkey = pkey

    def is_valid(self):
        return self.address and self.user and self.passwd and self.lcode and self.pkey


class WuBookServer(object):
    def __init__(self, login_data):
        self._server = None
        self._token = None
        self._login_data = login_data

    def __enter__(self):
        # we do nothing, api is lazy
        return self

    def __exit__(self, type, value, traceback):
        if self._server is not None:
            self.close()

    @property
    def server(self):
        if not self._login_data.is_valid():
            raise ChannelConnectorError(_("Invalid Channel Parameters!"))
        if self._server is None:
            try:
                self._server = xmlrpc.client.ServerProxy(self._login_data.address)
                res, tok = self._server.acquire_token(
                    self._login_data.user,
                    self._login_data.passwd,
                    self._login_data.pkey)
                if res == 0:
                    self._token = tok
                else:
                    self._server = None
            except Exception:
                self._server = None
                raise RetryableJobError(_("Can't connect with channel!"))
        return self._server

    @property
    def session_token(self):
        return self._token

    @property
    def lcode(self):
        return self._login_data.lcode

    def close(self):
        self._server.release_token(self._token)
        self._token = None
        self._server = None


class WuBookAdapter(AbstractComponent):
    _name = 'wubook.adapter'
    _inherit = 'hotel.channel.adapter'

    # === GENERAL
    def push_activation(self, base_url, security_token):
        rcode_a, results_a = self._server.push_activation(
            self._session_info[0],
            self._session_info[1],
            urljoin(base_url, "wubook/push/reservations/%s" % security_token),
            1)
        if rcode_a != 0:
            raise ChannelConnectorError(_("Can't activate push reservations"), {
                'message': results_a,
            })

        rcode_b, results_b = self._server.push_update_activation(
            self._session_info[0],
            self._session_info[1],
            urljoin(base_url, "wubook/push/rooms/%s" % security_token))
        if rcode_b != 0:
            raise ChannelConnectorError(_("Can't activate push rooms"), {
                'message': results_b,
            })

        return rcode_a == 0 and results_b == 0

    # === ROOMS
    def create_room(self, shortcode, name, capacity, price, availability, defboard,
                    names, descriptions, boards, min_price, max_price, rtype):
        rcode, results = self._server.new_room(
            self._session_info[0],
            self._session_info[1],
            0,
            name,
            capacity,
            price,
            availability,
            shortcode,
            defboard,
            names,
            descriptions,
            boards,
            int(rtype),
            # min_price, # Issue limit for min_price and max_price is they have to be higher than 5
            # max_price,
        )
        if rcode != 0:
            raise ChannelConnectorError(_("Can't create room in WuBook"), {
                'message': results,
            })
        return results

    def modify_room(self, channel_room_id, name, capacity, price, availability, scode, defboard,
                    names, descriptions, boards, min_price, max_price, rtype):
        rcode, results = self._server.mod_room(
            self._session_info[0],
            self._session_info[1],
            channel_room_id,
            name,
            capacity,
            price,
            availability,
            scode,
            defboard,
            names,
            descriptions,
            boards,
            min_price,
            max_price,
            int(rtype),
            0,
        )
        if rcode != 0:
            raise ChannelConnectorError(_("Can't modify room in WuBook"), {
                'message': results,
                'channel_id': channel_room_id,
            })
        return results

    def delete_room(self, channel_room_id):
        rcode, results = self._server.del_room(
            self._session_info[0],
            self._session_info[1],
            channel_room_id)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't delete room in WuBook"), {
                'message': results,
                'channel_id': channel_room_id,
            })
        return results

    def fetch_rooms(self, channel_room_id=0):
        rcode, results = self._server.fetch_rooms(
            self._session_info[0],
            self._session_info[1],
            channel_room_id)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't fetch room values from WuBook"), {
                'message': results,
                'channel_id': channel_room_id,
            })
        return results

    def fetch_rooms_values(self, date_from, date_to, rooms=False):
        # WuBook Knowledge Base:
        # 1.- The returned restrictions are the Standard Restrictions (default restriction plan).
        # The prices are related to the WuBook Parity, that is, pid = 0 (unless you modify it, linking the
        # WuBook Parity to a specific pricing plan).
        # 2.- You simply can't download room information for days in the past or more than 2 years in the future.
        date_today = fields.Date.today()
        date_2_years = (fields.Date.from_string(date_today) + timedelta(days=365) * 2).strftime(
            DEFAULT_SERVER_DATE_FORMAT)
        if date_from < date_today or date_from > date_2_years:
            date_from = date_today
        if date_to < date_today or date_to > date_2_years:
            date_to = date_today
        rcode, results = self._server.fetch_rooms_values(
            self._session_info[0],
            self._session_info[1],
            fields.Date.from_string(date_from).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            fields.Date.from_string(date_to).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            rooms)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't fetch rooms values from WuBook"), {
                'message': results,
            })
        return results

    def update_availability(self, rooms_avail):
        rcode, results = self._server.update_sparse_avail(
            self._session_info[0],
            self._session_info[1],
            rooms_avail)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't update rooms availability in WuBook"), {
                'message': results,
            })
        return results

    def corporate_fetch(self):
        rcode, results = self._server.corporate_fetchable_properties(self.TOKEN)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't call 'corporate_fetch' from WuBook"), {
                'message': results,
            })
        return results

    # === RESERVATIONS
    def create_reservation(self, channel_room_id, customer_name, email, city,
                           phone, address, country_code, checkin, checkout,
                           adults, children, notes=''):
        customer_name = _partner_split_name(customer_name)
        customer = {
            'lname': customer_name[0],
            'fname': customer_name[1],
            'email': email,
            'city': city,
            'phone': phone,
            'street': address,
            'country': country_code,
            'arrival_hour': fields.Datetime.from_string(checkin).strftime("%H:%M"),
            'notes': notes
        }
        rcode, results = self._server.new_reservation(
            self._session_info[0],
            self._session_info[1],
            fields.Date.from_string(checkin).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            fields.Date.from_string(checkout).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            {channel_room_id: [adults+children, 'nb']},
            customer,
            adults+children)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't create reservations in wubook"), {
                'message': results,
                'date_from': checkin,
                'date_to': checkout,
            })
        return results

    def cancel_reservation(self, channel_reservation_id, reason=""):
        rcode, results = self._server.cancel_reservation(
            self._session_info[0],
            self._session_info[1],
            channel_reservation_id,
            reason)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't cancel reservation in WuBook"), {
                'message': results,
                'channel_reservation_id': channel_reservation_id,
            })
        return results

    def fetch_new_bookings(self):
        rcode, results = self._server.fetch_new_bookings(
            self._session_info[0],
            self._session_info[1],
            1,
            0)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't process reservations from wubook"), {
                'message': results,
            })
        return results

    def fetch_bookings(self, dfrom, dto):
        rcode, results = self._server.fetch_bookings(
            self._session_info[0],
            self._session_info[1],
            fields.Date.from_string(dfrom).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            fields.Date.from_string(dto).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            0, # When oncreated is 0, the filter is applied against the arrival date
            1)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't process reservations from wubook"), {
                'message': results,
            })
        return results

    def fetch_booking(self, channel_reservation_id):
        rcode, results = self._server.fetch_booking(
            self._session_info[0],
            self._session_info[1],
            channel_reservation_id,
            1)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't process reservations from wubook"), {
                'message': results,
            })
        return results

    def mark_bookings(self, channel_reservation_ids):
        rcode, results = self._server.mark_bookings(
            self._session_info[0],
            self._session_info[1],
            channel_reservation_ids)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't mark as readed a reservation in wubook"), {
                'message': results,
                'channel_reservation_ids': str(channel_reservation_ids),
            })
        return results

    # === PRICE PLANS
    def create_plan(self, name, daily=1):
        rcode, results = self._server.add_pricing_plan(
            self._session_info[0],
            self._session_info[1],
            name,
            daily)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't add pricing plan to wubook"), {
                'message': results,
            })
        return results

    def create_vplan(self, name, pid, dtype, value):
        rcode, results = self._server.add_vplan(
            self._session_info[0],
            self._session_info[1],
            name,
            pid,
            dtype,
            value,
        )
        if rcode != 0:
            raise ChannelConnectorError(_("Can't add virtual pricing plan to wubook"), {
                'message': results,
            })
        return results

    def modify_vplan(self, pid, dtype, value):
        rcode, results = self._server.mod_vplans(
            self._session_info[0],
            self._session_info[1],
            [{'pid': pid,
              'variation': value,
              'variation_type': dtype
              }]
        )
        if rcode != 0:
            raise ChannelConnectorError(_("Can't modify virtual pricing plan in wubook"), {
                'message': results,
            })
        return results

    def delete_plan(self, channel_plan_id):
        rcode, results = self._server.del_plan(
            self._session_info[0],
            self._session_info[1],
            channel_plan_id)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't delete pricing plan from wubook"), {
                'message': results,
                'channel_plan_id': channel_plan_id,
            })
        return results

    def update_plan_name(self, channel_plan_id, new_name):
        rcode, results = self._server.update_plan_name(
            self._session_info[0],
            self._session_info[1],
            channel_plan_id,
            new_name)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't update pricing plan name in wubook"), {
                'message': results,
                'channel_plan_id': channel_plan_id,
            })
        return results

    def update_plan_prices(self, channel_plan_id, date_from, prices):
        rcode, results = self._server.update_plan_prices(
            self._session_info[0],
            self._session_info[1],
            channel_plan_id,
            fields.Date.from_string(date_from).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            prices)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't update pricing plan in wubook"), {
                'message': results,
                'channel_plan_id': channel_plan_id,
                'date_from': date_from,
            })
        return results

    def update_plan_periods(self, channel_plan_id, periods):
        rcode, results = self._server.update_plan_periods(
            self._session_info[0],
            self._session_info[1],
            channel_plan_id,
            periods)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't update pricing plan period in wubook"), {
                'message': results,
                'channel_plan_id': channel_plan_id,
            })
        return results

    def get_pricing_plans(self):
        rcode, results = self._server.get_pricing_plans(
            self._session_info[0],
            self._session_info[1])
        if rcode != 0:
            raise ChannelConnectorError(_("Can't get pricing plans from wubook"), {
                'message': results,
            })
        return results

    def fetch_plan_prices(self, channel_plan_id, date_from, date_to, rooms):
        rcode, results = self._server.fetch_plan_prices(
            self._session_info[0],
            self._session_info[1],
            channel_plan_id,
            fields.Date.from_string(date_from).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            fields.Date.from_string(date_to).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            rooms or [])
        if rcode != 0:
            raise ChannelConnectorError(_("Can't get pricing plans from wubook"), {
                'message': results,
                'channel_plan_id': channel_plan_id,
                'date_from': date_from,
                'date_to': date_to
            })
        return results

    # === RESTRICTIONS
    def rplan_rplans(self):
        rcode, results = self._server.rplan_rplans(
            self._session_info[0],
            self._session_info[1])
        if rcode != 0:
            raise ChannelConnectorError(_("Can't fetch restriction plans from wubook"), {
                'message': results,
            })
        return results

    def wired_rplan_get_rplan_values(self, date_from, date_to, channel_restriction_plan_id):
        # fetch_rooms_values returns a KV structure for each room and for each day
        # corresponding to the default WuBook restriction plan with rpid=0.
        if int(channel_restriction_plan_id) == 0:
            rcode, results = self._server.fetch_rooms_values(
                self._session_info[0],
                self._session_info[1],
                fields.Date.from_string(date_from).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                fields.Date.from_string(date_to).strftime(DEFAULT_WUBOOK_DATE_FORMAT))
            # prepare KV structure as expeced by _generate_restriction_items
            for room_type in results:
                restrictions = results[room_type]
                date = fields.Date.from_string(date_from)
                for daily_restriction in restrictions:
                    daily_restriction.update({'date': date.strftime(DEFAULT_WUBOOK_DATE_FORMAT)})
                    date = date + timedelta(days=1)
            results = {'0': results}
        else:
            # WuBook Knowledge Base: restriction plan besides the wubook restrictions
            # are not returned by wired_rplan_get_rplan_values
            rcode, results = self._server.wired_rplan_get_rplan_values(
                self._session_info[0],
                self._session_info[1],
                '1.1',
                fields.Date.from_string(date_from).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                fields.Date.from_string(date_to).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                int(channel_restriction_plan_id))
        if rcode != 0:
            raise ChannelConnectorError(_("Can't fetch restriction plans from wubook"), {
                'message': results,
                'channel_restriction_plan_id': channel_restriction_plan_id,
                'date_from': date_from,
                'date_to': date_to,
            })
        return results

    def update_rplan_values(self, channel_restriction_plan_id, date_from, values):
        rcode, results = self._server.rplan_update_rplan_values(
            self._session_info[0],
            self._session_info[1],
            channel_restriction_plan_id,
            fields.Date.from_string(date_from).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            values)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't update plan restrictions on wubook"), {
                'message': results,
                'channel_restriction_plan_id': channel_restriction_plan_id,
                'date_from': date_from,
            })
        return results

    def create_rplan(self, name, compact=False):
        rcode, results = self._server.rplan_add_rplan(
            self._session_info[0],
            self._session_info[1],
            name,
            compact and 1 or 0)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't create plan restriction in wubook"), {
                'message': results,
            })
        return results

    def rename_rplan(self, channel_restriction_plan_id, new_name):
        rcode, results = self._server.rplan_rename_rplan(
            self._session_info[0],
            self._session_info[1],
            channel_restriction_plan_id,
            new_name)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't rename plan restriction in wubook"), {
                'message': results,
                'channel_restriction_plan_id': channel_restriction_plan_id,
            })
        return results

    def delete_rplan(self, channel_restriction_plan_id):
        rcode, results = self._server.rplan_del_rplan(
            self._session_info[0],
            self._session_info[1],
            channel_restriction_plan_id)
        if rcode != 0:
            raise ChannelConnectorError(_("Can't delete plan restriction on wubook"), {
                'message': results,
                'channel_restriction_plan_id': channel_restriction_plan_id,
            })
        return results

    def get_channels_info(self):
        results = self._server.get_channels_info(self._session_info[0])
        if not any(results):
            raise ChannelConnectorError(_("Can't import channels info from wubook"), {
                'message': results,
            })
        return results
