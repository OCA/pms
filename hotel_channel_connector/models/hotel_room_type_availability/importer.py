# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo import api


class HotelRoomTypeAvailabilityImporter(Component):
    _name = 'channel.hotel.room.type.availability.importer'
    _inherit = 'hotel.channel.importer'
    _apply_on = ['channel.hotel.room.type.availability']
    _usage = 'hotel.room.type.availability.importer'

    @api.model
    def import_availability_values(self, date_from, date_to):
        raise NotImplementedError
