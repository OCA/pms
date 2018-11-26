# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class HotelRoomTypeRestrictionAdapter(Component):
    _name = 'channel.hotel.room.type.restriction.adapter'
    _inherit = 'wubook.adapter'
    _apply_on = 'channel.hotel.room.type.restriction'

    def rplan_rplans(self):
        return super(HotelRoomTypeRestrictionAdapter, self).rplan_rplans()

    def create_rplan(self, name):
        return super(HotelRoomTypeRestrictionAdapter, self).create_rplan(name)

    def delete_rplan(self, external_id):
        return super(HotelRoomTypeRestrictionAdapter, self).delete_rplan(external_id)

    def rename_rplan(self, external_id, new_name):
        return super(HotelRoomTypeRestrictionAdapter, self).rename_rplan(external_id, new_name)
