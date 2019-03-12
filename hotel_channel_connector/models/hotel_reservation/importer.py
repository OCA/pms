# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api
from odoo.addons.component.core import Component


class HotelReservationImporter(Component):
    _name = 'channel.hotel.reservation.importer'
    _inherit = 'hotel.channel.importer'
    _apply_on = ['channel.hotel.reservation']
    _usage = 'hotel.reservation.importer'

    @api.model
    def fetch_booking(self, channel_reservation_id):
        raise NotImplementedError

    def fetch_new_bookings(self):
        raise NotImplementedError

    def fetch_bookings(self, dfrom, dto):
        raise NotImplementedError
