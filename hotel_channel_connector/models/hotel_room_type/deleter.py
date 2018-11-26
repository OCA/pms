# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo import api


class HotelRoomTypeDeleter(Component):
    _name = 'channel.hotel.room.type.deleter'
    _inherit = 'hotel.channel.deleter'
    _apply_on = ['channel.hotel.room.type']
    _usage = 'hotel.room.type.deleter'

    @api.model
    def delete_room(self, binding):
        raise NotImplementedError
