# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo import fields, api, _
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)


class HotelReservationImporter(Component):
    _name = 'channel.hotel.reservation.importer'
    _inherit = 'hotel.channel.importer'
    _apply_on = ['channel.hotel.reservation']
    _usage = 'hotel.reservation.importer'

    def fetch_new_bookings(self):
        try:
            results = self.backend_adapter.fetch_new_bookings()
            processed_rids, errors, checkin_utc_dt, checkout_utc_dt = \
                self._generate_reservations(results)
            if any(processed_rids):
                uniq_rids = list(set(processed_rids))
                rcodeb, resultsb = self.backend_adapter.mark_bookings(uniq_rids)
                if rcodeb != 0:
                    self.create_issue(
                        'wubook',
                        _("Problem trying mark bookings (%s)") % str(processed_rids),
                        '')
            # Update Odoo availability (don't wait for wubook)
            # This cause abuse service in first import!!
            if checkin_utc_dt and checkout_utc_dt:
                self.backend_adapter.fetch_rooms_values(
                    checkin_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    checkout_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT))
        except ChannelConnectorError as err:
            self.create_issue(
                'reservation',
                _("Can't process reservations from wubook"),
                err.data['message'])
            return False
        return True
