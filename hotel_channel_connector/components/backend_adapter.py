# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class HotelChannelInterfaceAdapter(AbstractComponent):
    _name = 'hotel.channel.adapter'
    _inherit = ['base.backend.adapter', 'base.hotel.channel.connector']
    _usage = 'backend.adapter'

    def push_activation(self, base_url, security_token):
        raise NotImplementedError

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

    def fetch_bookings(self, dfrom, dto):
        raise NotImplementedError

    def fetch_booking(self, channel_reservation_id):
        raise NotImplementedError

    def mark_bookings(self, channel_reservation_ids):
        raise NotImplementedError

    def create_plan(self, name, daily=1):
        raise NotImplementedError

    def create_vplan(self, name, pid, dtype, value):
        raise NotImplementedError

    def modify_vplan(self, pid, dtype, value):
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
            channel_server = getattr(self.work, 'channel_api')
        except AttributeError:
            raise AttributeError(
                'You must provide a channel_api attribute with a '
                'ChannelServer instance to be able to use the '
                'Backend Adapter.'
            )
        return channel_server.server

    @property
    def _session_info(self):
        try:
            channel_server = getattr(self.work, 'channel_api')
        except AttributeError:
            raise AttributeError(
                'You must provide a channel_api attribute with a '
                'ChannelServer instance to be able to use the '
                'Backend Adapter.'
            )
        return (channel_server.session_token, channel_server._login_data.lcode)
