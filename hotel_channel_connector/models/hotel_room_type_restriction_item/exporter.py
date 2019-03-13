# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo import api


class HotelRoomTypeRestrictionItemExporter(Component):
    _name = 'channel.hotel.room.type.restriction.item.exporter'
    _inherit = 'hotel.channel.exporter'
    _apply_on = ['channel.hotel.room.type.restriction.item']
    _usage = 'hotel.room.type.restriction.item.exporter'

    @api.model
    def push_restriction(self):
        raise NotImplementedError

    @api.model
    def close_online_sales(self):
        raise NotImplementedError