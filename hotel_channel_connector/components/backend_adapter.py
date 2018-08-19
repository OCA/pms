from odoo.addons.component.core import AbstractComponent
from odoo.addons.queue_job.exception import RetryableJobError
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
from odoo.addons.payment.models.payment_acquirer import _partner_split_name
from odoo.addons.hotel import date_utils

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

    @property
    def server(self):
        if self._server is None and self._login_data.is_valid():
            try:
                self._server = xmlrpclib.Server(self._login_data.address)
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
                raise RetryableJobError("Can't connect with channel!")
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

class HotelChannelInterfaceAdapter(AbstractComponent):
    _name = 'hotel.channel.interface.adapter'
    _inherit = ['base.backend.adapter', 'base.hotel.channel.connector']
    _usage = 'backend.adapter'

    def create_room(self, shortcode, name, capacity, price, availability):
        raise NotImplementedError

    def modify_room(self, channel_room_id, name, capacity, price, availability, scode):
        raise NotImplementedError

    def delete_room(self, channel_room_id):
        raise NotImplementedError

    def fetch_rooms(self, channel_room_id=0):
        raise NotImplementedError

    def fetch_rooms_values(self, date_from, date_to, rooms=False):
        raise NotImplementedError

    def update_availability(self, rooms_avail):
        raise NotImplementedError

    def corporate_fetch(self):
        raise NotImplementedError

    def create_reservation(self, channel_room_id, customer_name, email, city,
                           phone, address, country_code, checkin, checkout,
                           adults, children, notes=''):
        raise NotImplementedError

    def cancel_reservation(self, channel_reservation_id, reason=""):
        raise NotImplementedError

    def fetch_new_bookings(self):
        raise NotImplementedError

    def fetch_booking(self, channel_reservation_id):
        raise NotImplementedError

    def mark_bookings(self, channel_reservation_ids):
        raise NotImplementedError

    def create_plan(self, name, daily=1):
        raise NotImplementedError

    def delete_plan(self, channel_plan_id):
        raise NotImplementedError

    def update_plan_name(self, channel_plan_id, new_name):
        raise NotImplementedError

    def update_plan_prices(self, channel_plan_id, date_from, prices):
        raise NotImplementedError

    def update_plan_periods(self, channel_plan_id, periods):
        raise NotImplementedError

    def get_pricing_plans(self):
        raise NotImplementedError

    def fetch_plan_prices(self, channel_plan_id, date_from, date_to, rooms):
        raise NotImplementedError

    def rplan_rplans(self):
        raise NotImplementedError

    def wired_rplan_get_rplan_values(self, date_from, date_to, channel_restriction_plan_id):
        raise NotImplementedError

    def update_rplan_values(self, channel_restriction_plan_id, date_from, values):
        raise NotImplementedError

    def create_rplan(self, name, compact=False):
        raise NotImplementedError

    def rename_rplan(self, channel_restriction_plan_id, new_name):
        raise NotImplementedError

    def delete_rplan(self, channel_restriction_plan_id):
        raise NotImplementedError

    def get_channels_info(self):
        raise NotImplementedError

    @property
    def _server(self):
        try:
            channel_server = getattr(self.work, 'hotel_channel_server')
        except AttributeError:
            raise AttributeError(
                'You must provide a hotel_channel_server attribute with a '
                'WuBookServer instance to be able to use the '
                'Backend Adapter.'
            )
        return channel_server.server

    @property
    def _session_info(self):
        try:
            channel_server = getattr(self.work, 'hotel_channel_server')
        except AttributeError:
            raise AttributeError(
                'You must provide a hotel_channel_server attribute with a '
                'WuBookServer instance to be able to use the '
                'Backend Adapter.'
            )
        return (channel_server.session_token, channel_server.lcode)

class WuBookAdapter(AbstractComponent):
    _name = 'wubook.adapter'
    _inherit = 'hotel.channel.interface.adapter'

    # === ROOMS
    def create_room(self, shortcode, name, capacity, price, availability):
        rcode, results = self._server.new_room(
            self._session_info[0],
            self._session_info[1],
            0,
            name,
            capacity,
            price,
            availability,
            shortcode[:4],
            'nb'    # TODO: Complete this part
            # rtype=('name' in vals and vals['name'] and 3) or 1
        )
        if rcode != 0:
            raise ValidationError(_("Can't create room in WuBook"), {
                'message': results,
            })
        return results

    def modify_room(self, channel_room_id, name, capacity, price, availability, scode):
        rcode, results = self._server.mod_room(
            self._session_info[0],
            self._session_info[1],
            channel_room_id,
            name,
            capacity,
            price,
            availability,
            scode,
            'nb'
            # rtype=('name' in vals and vals['name'] and 3) or 1
        )
        if rcode != 0:
            raise ValidationError(_("Can't modify room in WuBook"), {
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
            raise ValidationError(_("Can't delete room in WuBook"), {
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
            raise ValidationError(_("Can't fetch room values from WuBook"), {
                'message': results,
                'channel_id': channel_room_id,
            })
        return results

    def fetch_rooms_values(self, date_from, date_to, rooms=False):
        rcode, results = self._server.fetch_rooms_values(
            self._session_info[0],
            self._session_info[1],
            date_utils.get_datetime(date_from).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            date_utils.get_datetime(date_to).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            rooms)
        if rcode != 0:
            raise ValidationError(_("Can't fetch rooms values from WuBook"), {
                'message': results,
            })
        return results

    def update_availability(self, rooms_avail):
        rcode, results = self._server.update_sparse_avail(
            self._session_info[0],
            self._session_info[1],
            rooms_avail)
        if rcode != 0:
            raise ValidationError(_("Can't update rooms availability in WuBook"), {
                'message': results,
            })
        return results

    def corporate_fetch(self):
        rcode, results = self._server.corporate_fetchable_properties(self.TOKEN)
        if rcode != 0:
            raise ValidationError(_("Can't call 'corporate_fetch' from WuBook"), {
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
            'arrival_hour': date_utils.get_datetime(checkin).strftime("%H:%M"),
            'notes': notes
        }
        rcode, results = self._server.new_reservation(
            self._session_info[0],
            self._session_info[1],
            date_utils.get_datetime(checkin).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            date_utils.get_datetime(checkout).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            {channel_room_id: [adults+children, 'nb']},
            customer,
            adults+children)
        if rcode != 0:
            raise ValidationError(_("Can't create reservations in wubook"), {
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
            raise ValidationError(_("Can't cancel reservation in WuBook"), {
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
            raise ValidationError(_("Can't process reservations from wubook"), {
                'message': results,
            })
        return results

    def fetch_booking(self, channel_reservation_id):
        rcode, results = self.backend_adapter.fetch_booking(
            self._session_info[0],
            self._session_info[1],
            channel_reservation_id)
        if rcode != 0:
            raise ValidationError(_("Can't process reservation from wubook"), {
                'message': results,
            })
        return results

    def mark_bookings(self, channel_reservation_ids):
        init_connection = self._context.get('init_connection', True)
        if init_connection:
            if not self.init_connection():
                return False
        rcode, results = self._server.mark_bookings(
            self._session_info[0],
            self._session_info[1],
            channel_reservation_ids)
        if rcode != 0:
            raise ValidationError(_("Can't mark as readed a reservation in wubook"), {
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
            raise ValidationError(_("Can't add pricing plan to wubook"), {
                'message': results,
            })
        return results

    def delete_plan(self, channel_plan_id):
        rcode, results = self._server.del_plan(
            self._session_info[0],
            self._session_info[1],
            channel_plan_id)
        if rcode != 0:
            raise ValidationError(_("Can't delete pricing plan from wubook"), {
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
            raise ValidationError(_("Can't update pricing plan name in wubook"), {
                'message': results,
                'channel_plan_id': channel_plan_id,
            })
        return results

    def update_plan_prices(self, channel_plan_id, date_from, prices):
        rcode, results = self._server.update_plan_prices(
            self._session_info[0],
            self._session_info[1],
            channel_plan_id,
            date_utils.get_datetime(date_from).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            prices)
        if rcode != 0:
            raise ValidationError(_("Can't update pricing plan in wubook"), {
                'message': results,
                'channel_plan_id': channel_plan_id,
                'date_from': date_from,
            })
        return results

    def update_plan_periods(self, channel_plan_id, periods):
        rcode, results = self.SERVER.update_plan_periods(
            self._session_info[0],
            self._session_info[1],
            channel_plan_id,
            periods)
        if rcode != 0:
            raise ValidationError(_("Can't update pricing plan period in wubook"), {
                'message': results,
                'channel_plan_id': channel_plan_id,
            })
        return results

    def get_pricing_plans(self):
        rcode, results = self.SERVER.get_pricing_plans(
            self._session_info[0],
            self._session_info[1])
        if rcode != 0:
            raise ValidationError(_("Can't get pricing plans from wubook"), {
                'message': results,
            })
        return results

    def fetch_plan_prices(self, channel_plan_id, date_from, date_to, rooms):
        rcode, results = self._server.fetch_plan_prices(
            self._session_info[0],
            self._session_info[1],
            channel_plan_id,
            date_utils(date_from).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            date_utils(date_to).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            rooms or [])
        if rcode != 0:
            raise ValidationError(_("Can't get pricing plans from wubook"), {
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
            raise ValidationError(_("Can't fetch restriction plans from wubook"), {
                'message': results,
            })
        return results

    def wired_rplan_get_rplan_values(self, date_from, date_to, channel_restriction_plan_id):
        rcode, results = self._server.wired_rplan_get_rplan_values(
            self._session_info[0],
            self._session_info[1],
            date_utils(date_from).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            date_utils(date_to).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            channel_restriction_plan_id)
        if rcode != 0:
            raise ValidationError(_("Can't fetch restriction plans from wubook"), {
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
            date_utils(date_from).strftime(DEFAULT_WUBOOK_DATE_FORMAT),
            values)
        if rcode != 0:
            raise ValidationError(_("Can't update plan restrictions on wubook"), {
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
            raise ValidationError(_("Can't create plan restriction in wubook"), {
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
            raise ValidationError(_("Can't rename plan restriction in wubook"), {
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
            raise ValidationError(_("Can't delete plan restriction on wubook"), {
                'message': results,
                'channel_restriction_plan_id': channel_restriction_plan_id,
            })
        return results

    def get_channels_info(self):
        results = self._server.get_channels_info(self._session_info[0])
        if not any(results):
            raise ValidationError(_("Can't import channels info from wubook"), {
                'message': results,
            })
        return results
