# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo import api


class HotelRoomTypeRestrictionImporter(Component):
    _name = 'channel.hotel.room.type.restriction.item.importer'
    _inherit = 'hotel.channel.importer'
    _apply_on = ['channel.hotel.room.type.restriction.item']
    _usage = 'hotel.room.type.restriction.item.importer'

    # FIXME: Reduce Nested Loops!!
    @api.model
    def _generate_restriction_items(self, plan_restrictions):
        raise NotImplementedError

    @api.model
    def import_restriction_values(self, date_from, date_to, channel_restr_id=False):
        raise NotImplementedError
