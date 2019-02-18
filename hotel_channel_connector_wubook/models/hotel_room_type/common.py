# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from odoo.addons.component.core import Component

class HotelRoomTypeAdapter(Component):
    _name = 'channel.hotel.room.type.adapter'
    _inherit = 'wubook.adapter'
    _apply_on = 'channel.hotel.room.type'

    def create_room(self, shortcode, name, capacity, price, availability, defboard,
                    names, descriptions, boards, min_price, max_price, rtype):
        return super(HotelRoomTypeAdapter, self).create_room(
            shortcode, name, capacity, price, availability, defboard,
            names, descriptions, boards, min_price, max_price, rtype)

    def fetch_rooms(self):
        return super(HotelRoomTypeAdapter, self).fetch_rooms()

    def modify_room(self, channel_room_id, name, capacity, price, availability, scode, defboard,
                    names, descriptions, boards, min_price, max_price, rtype):
        return super(HotelRoomTypeAdapter, self).modify_room(
            channel_room_id, name, capacity, price, availability, scode, defboard,
            names, descriptions, boards, min_price, max_price, rtype)

    def delete_room(self, channel_room_id):
        return super(HotelRoomTypeAdapter, self).delete_room(channel_room_id)


class ChannelHotelRoomType(models.Model):
    _inherit = 'hotel.room.type'

    @api.constrains('min_price', 'max_price')
    def _check_min_max_price(self):
        for record in self:
            if record.min_price < 5 or record.max_price < 5:
                msg = _("The channel manager limits the minimum value of min price and max price to 5.")
                raise ValidationError(msg)
