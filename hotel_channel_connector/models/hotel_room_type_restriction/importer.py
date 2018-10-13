# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta
from odoo.exceptions import ValidationError
from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.hotel import date_utils
from odoo import fields, api, _
_logger = logging.getLogger(__name__)


class HotelRoomTypeRestrictionImporter(Component):
    _name = 'channel.hotel.room.type.restriction.importer'
    _inherit = 'hotel.channel.importer'
    _apply_on = ['channel.hotel.room.type.restriction']
    _usage = 'hotel.room.type.restriction.importer'


class HotelRoomTypeRestrictionImportMapper(Component):
    _name = 'channel.hotel.room.type.restriction.import.mapper'
    _inherit = 'channel.import.mapper'
    _apply_on = 'channel.hotel.room.type.restriction'

    direct = [
        ('no_ota', 'no_ota'),
        ('booked', 'booked'),
        ('avail', 'avail'),
        ('room_type_id', 'room_type_id'),
        ('date', 'date')
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}
