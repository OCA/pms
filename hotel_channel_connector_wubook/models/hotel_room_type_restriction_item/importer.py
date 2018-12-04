# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime
from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo.addons.connector.components.mapper import mapping, only_create
from odoo.addons.hotel_channel_connector_wubook.components.backend_adapter import (
    DEFAULT_WUBOOK_DATE_FORMAT)
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import api, fields
_logger = logging.getLogger(__name__)


class HotelRoomTypeRestrictionImporter(Component):
    _inherit = 'channel.hotel.room.type.restriction.item.importer'

    # FIXME: Reduce Nested Loops!!
    @api.model
    def _generate_restriction_items(self, plan_restrictions):
        channel_hotel_room_type_obj = self.env['channel.hotel.room.type']
        channel_reserv_restriction_obj = self.env['channel.hotel.room.type.restriction']
        channel_restriction_item_obj = self.env['channel.hotel.room.type.restriction.item']
        restriction_item_mapper = self.component(
            usage='import.mapper',
            model_name='channel.hotel.room.type.restriction.item')
        _logger.info("==[CHANNEL->ODOO]==== RESTRICTIONS ==")
        _logger.info(plan_restrictions)
        for k_rpid, v_rpid in plan_restrictions.items():
            channel_restriction_id = channel_reserv_restriction_obj.search([
                ('backend_id', '=', self.backend_record.id),
                ('external_id', '=', k_rpid),
            ], limit=1)
            if channel_restriction_id:
                for k_rid, v_rid in v_rpid.items():
                    channel_room_type = channel_hotel_room_type_obj.search([
                        ('backend_id', '=', self.backend_record.id),
                        ('external_id', '=', k_rid),
                    ], limit=1)
                    if channel_room_type:
                        for item in v_rid:
                            map_record = restriction_item_mapper.map_record(item)
                            date_dt = datetime.strptime(item['date'], DEFAULT_WUBOOK_DATE_FORMAT)
                            date_str = date_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                            channel_restriction_item = channel_restriction_item_obj.search([
                                ('backend_id', '=', self.backend_record.id),
                                ('restriction_id', '=', channel_restriction_id.odoo_id.id),
                                ('date', '=', date_str),
                                ('applied_on', '=', '0_room_type'),
                                ('room_type_id', '=', channel_room_type.odoo_id.id)
                            ], limit=1)
                            item.update({
                                'date': date_str,
                                'room_type_id': channel_room_type.odoo_id.id,
                                'restriction_id': channel_restriction_id.odoo_id.id,
                            })
                            if channel_restriction_item:
                                channel_restriction_item.with_context({
                                    'connector_no_export': True
                                }).write(map_record.values())
                            else:
                                channel_restriction_item = channel_restriction_item_obj.with_context({
                                    'connector_no_export': True
                                }).create(map_record.values(for_create=True))
                            channel_restriction_item.channel_pushed = True

    @api.model
    def import_restriction_values(self, date_from, date_to, channel_restr_id=False):
        channel_restr_plan_id = int(channel_restr_id) if channel_restr_id else False
        try:
            results = self.backend_adapter.wired_rplan_get_rplan_values(
                date_from,
                date_to,
                int(channel_restr_plan_id))
        except ChannelConnectorError as err:
            self.create_issue(
                section='restriction',
                internal_message=str(err),
                channel_message=err.data['message'],
                channel_object_id=channel_restr_id,
                dfrom=date_from, dto=date_to)
        else:
            if any(results):
                self._generate_restriction_items(results)


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
        ('date', 'date'),
    ]

    @only_create
    @mapping
    def channel_pushed(self, record):
        return {'channel_pushed': True}

    @mapping
    def room_type_id(self, record):
        return {'room_type_id': record['room_type_id']}

    @mapping
    def restriction_id(self, record):
        return {'restriction_id': record['restriction_id']}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def sync_date(self, record):
        return {'sync_date': fields.Datetime.now()}
