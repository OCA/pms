# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import ValidationError
from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo.addons.connector.components.mapper import mapping
from odoo import fields, api, _
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)


class HotelRoomTypeImporter(Component):
    _name = 'channel.hotel.room.type.importer'
    _inherit = 'hotel.channel.importer'
    _apply_on = ['channel.hotel.room.type']
    _usage = 'hotel.room.type.importer'

    def _import_record(self, external_id, job_options=None, **kwargs):
        return super(HotelRoomTypeImporter, self)._import_record(external_id)

    @api.model
    def get_rooms(self):
        count = 0
        try:
            results = self.backend_adapter.fetch_rooms()

            channel_room_type_obj = self.env['channel.hotel.room.type']
            room_mapper = self.component(usage='import.mapper',
                                         model_name='channel.hotel.room.type')
            count = len(results)
            for room in results:
                map_record = room_mapper.map_record(room)
                room_bind = channel_room_type_obj.search([
                    ('channel_room_id', '=', room['id'])
                ], limit=1)
                if room_bind:
                    room_bind.with_context({'wubook_action': False}).write(map_record.values())
                else:
                    room_bind = channel_room_type_obj.with_context({'wubook_action': False}).create(
                        map_record.values(for_create=True))
                room_bind.odoo_id.write({
                    'list_price': room['price'],
                    'name': room['name'],
                })
        except ChannelConnectorError as err:
            self.create_issue('room', _("Can't import rooms from WuBook"), err.data['message'])

        return count

    @api.model
    def fetch_rooms_values(self, dfrom, dto, rooms=False,
                           set_max_avail=False):
        # Sanitize Dates
        now_dt = date_utils.now()
        dfrom_dt = date_utils.get_datetime(dfrom)
        dto_dt = date_utils.get_datetime(dto)
        if dto_dt < now_dt:
            return True
        if dfrom_dt < now_dt:
            dfrom_dt = now_dt
        if dfrom_dt > dto_dt:
            dfrom_dt, dto_dt = dto_dt, dfrom_dt

        try:
            results = self.backend_adapter.fetch_rooms_values(
                dfrom_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                dto_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                rooms)
            self._generate_room_values(dfrom, dto, results,
                                       set_max_avail=set_max_avail)
        except ChannelConnectorError as err:
            self.create_issue('room', _("Can't fetch rooms values from WuBook"),
                              err.data['message'], dfrom=dfrom, dto=dto)
            return False
        return True


class HotelRoomTypeImportMapper(Component):
    _name = 'channel.hotel.room.type.import.mapper'
    _inherit = 'channel.import.mapper'
    _apply_on = 'channel.hotel.room.type'

    direct = [
        ('id', 'channel_room_id'),
        ('shortname', 'channel_short_code'),
        ('occupancy', 'ota_capacity'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}
