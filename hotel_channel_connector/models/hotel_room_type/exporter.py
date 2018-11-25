# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo import api


class HotelRoomTypeExporter(Component):
    _name = 'channel.hotel.room.type.exporter'
    _inherit = 'hotel.channel.exporter'
    _apply_on = ['channel.hotel.room.type']
    _usage = 'hotel.room.type.exporter'

    @api.model
    def modify_room(self, binding):
        raise NotImplementedError

    @api.model
    def create_room(self, binding):
        raise NotImplementedError
