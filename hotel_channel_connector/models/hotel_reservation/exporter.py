# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo import api


class HotelReservationExporter(Component):
    _name = 'channel.hotel.reservation.exporter'
    _inherit = 'hotel.channel.exporter'
    _apply_on = ['channel.hotel.reservation']
    _usage = 'hotel.reservation.exporter'

    @api.model
    def cancel_reservation(self, binding):
        raise NotImplementedError

    @api.model
    def mark_booking(self, binding):
        raise NotImplementedError

    @api.model
    def mark_bookings(self, external_ids):
        raise NotImplementedError
