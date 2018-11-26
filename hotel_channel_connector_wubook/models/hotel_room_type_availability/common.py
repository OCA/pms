# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class HotelRoomTypeAvailabilityAdapter(Component):
    _name = 'channel.hotel.room.type.availability.adapter'
    _inherit = 'wubook.adapter'
    _apply_on = 'channel.hotel.room.type.availability'

    def fetch_rooms_values(self, date_from, date_to, rooms=False):
        return super(HotelRoomTypeAvailabilityAdapter, self).fetch_rooms_values(
            date_from,
            date_to,
            rooms)

    def update_availability(self, rooms_avail):
        return super(HotelRoomTypeAvailabilityAdapter, self).update_availability(
            rooms_avail)
