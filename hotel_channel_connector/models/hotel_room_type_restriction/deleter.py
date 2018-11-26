# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo import api


class HotelRoomTypeRestrictionDeleter(Component):
    _name = 'channel.hotel.room.type.restriction.deleter'
    _inherit = 'hotel.channel.deleter'
    _apply_on = ['channel.hotel.room.type.restriction']
    _usage = 'hotel.room.type.restriction.deleter'

    @api.model
    def delete_rplan(self, binding):
        raise NotImplementedError
