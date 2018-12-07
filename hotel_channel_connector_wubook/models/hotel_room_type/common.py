# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class HotelRoomTypeAdapter(Component):
    _name = 'channel.hotel.room.type.adapter'
    _inherit = 'wubook.adapter'
    _apply_on = 'channel.hotel.room.type'

    def create_room(self, shortcode, name, capacity, price, availability, defboard, rtype):
        return super(HotelRoomTypeAdapter, self).create_room(
            shortcode, name, capacity, price, availability, defboard, rtype)

    def fetch_rooms(self):
        return super(HotelRoomTypeAdapter, self).fetch_rooms()

    def modify_room(self, channel_room_id, name, capacity, price, availability, scode, defboard, rtype):
        return super(HotelRoomTypeAdapter, self).modify_room(
            channel_room_id, name, capacity, price, availability, scode, defboard, rtype)

    def delete_room(self, channel_room_id):
        return super(HotelRoomTypeAdapter, self).delete_room(channel_room_id)
