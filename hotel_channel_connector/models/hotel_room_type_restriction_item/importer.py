# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta
from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo.addons.connector.components.mapper import mapping, only_create
from odoo.addons.hotel import date_utils
from odoo import fields, api, _
_logger = logging.getLogger(__name__)


class HotelRoomTypeRestrictionImporter(Component):
    _name = 'channel.hotel.room.type.restriction.item.importer'
    _inherit = 'hotel.channel.importer'
    _apply_on = ['channel.hotel.room.type.restriction.item']
    _usage = 'hotel.room.type.restriction.item.importer'

class HotelRoomTypeRestrictionItemImportMapper(Component):
    _name = 'channel.hotel.room.type.restriction.item.import.mapper'
    _inherit = 'channel.import.mapper'
    _apply_on = 'channel.hotel.room.type.restriction.item'

    direct = [
        ('min_stay', 'min_stay'),
        ('min_stay_arrival', 'min_stay_arrival'),
        ('max_stay', 'max_stay'),
        ('max_stay_arrival', 'max_stay_arrival'),
        ('closed', 'closed'),
        ('closed_departure', 'closed_departure'),
        ('closed_arrival', 'closed_arrival'),
        ('room_type_id', 'room_type_id'),
        ('date', 'date'),
    ]

    @only_create
    @mapping
    def applied_on(self, record):
        return {'applied_on': '0_room_type'}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}
