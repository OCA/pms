# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo import api


class HotelRoomTypeRestrictionExporter(Component):
    _name = 'channel.hotel.room.type.restriction.exporter'
    _inherit = 'hotel.channel.exporter'
    _apply_on = ['channel.hotel.room.type.restriction']
    _usage = 'hotel.room.type.restriction.exporter'

    @api.model
    def rename_rplan(self, binding):
        raise NotImplementedError

    @api.model
    def create_rplan(self, binding):
        raise NotImplementedError
