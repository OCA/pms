# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta
from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo.addons.hotel_channel_connector.components.backend_adapter import (
    DEFAULT_WUBOOK_DATE_FORMAT)
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import fields, api, _
_logger = logging.getLogger(__name__)

class HotelRoomTypeRestrictionItemExporter(Component):
    _name = 'channel.hotel.room.type.restriction.item.exporter'
    _inherit = 'hotel.channel.exporter'
    _apply_on = ['channel.hotel.room.type.restriction.item']
    _usage = 'hotel.room.type.restriction.item.exporter'

    @api.model
    def update_restriction(self, binding):
        if any(binding.restriction_id.channel_bind_ids):
            # FIXME: Supossed that only exists one channel connector per record
            binding.channel_pushed = True
            return self.backend_adapter.update_rplan_values(
                binding.restriction_id.channel_bind_ids[0].external_id,
                binding.date,
                {
                    'min_stay': binding.min_stay or 0,
                    'min_stay_arrival': binding.min_stay_arrival or 0,
                    'max_stay': binding.max_stay or 0,
                    'max_stay_arrival': binding.max_stay_arrival or 0,
                    'closed': binding.closed and 1 or 0,
                    'closed_arrival': binding.closed_arrival and 1 or 0,
                    'closed_departure': binding.closed_departure and 1 or 0,
                })

    @api.model
    def push_restriction(self):
        channel_room_type_rest_obj = self.env['channel.hotel.room.type.restriction']
        channel_rest_item_obj = self.env['channel.hotel.room.type.restriction.item']
        unpushed = channel_rest_item_obj.search([
            ('channel_pushed', '=', False),
            ('date', '>=', fields.Date.today())
        ], order="date ASC")
        if any(unpushed):
            date_start = fields.Date.from_string(unpushed[0].date)
            date_end = fields.Date.from_string(unpushed[-1].date)
            days_diff = (date_end-date_start).days + 1
            restrictions = {}
            channel_restr_plan_ids = channel_room_type_rest_obj.search([])
            for rp in channel_restr_plan_ids:
                restrictions.update({rp.external_id: {}})
                unpushed_rp = channel_rest_item_obj.search([
                    ('channel_pushed', '=', False),
                    ('restriction_id', '=', rp.odoo_id.id)
                ])
                room_type_ids = unpushed_rp.mapped('room_type_id')
                for room_type in room_type_ids:
                    if any(room_type.channel_bind_ids):
                        # FIXME: Supossed that only exists one channel connector per record
                        room_type_external_id = room_type.channel_bind_ids[0].external_id
                        restrictions[rp.external_id].update({
                            room_type_external_id: [],
                        })
                        for i in range(0, days_diff):
                            ndate_dt = date_start + timedelta(days=i)
                            restr = room_type.get_restrictions(
                                ndate_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                                rp.odoo_id.id)
                            if restr:
                                restrictions[rp.external_id][room_type_external_id].append({
                                    'min_stay': restr.min_stay or 0,
                                    'min_stay_arrival': restr.min_stay_arrival or 0,
                                    'max_stay': restr.max_stay or 0,
                                    'max_stay_arrival': restr.max_stay_arrival or 0,
                                    'closed': restr.closed and 1 or 0,
                                    'closed_arrival': restr.closed_arrival and 1 or 0,
                                    'closed_departure': restr.closed_departure and 1 or 0,
                                })
                            else:
                                restrictions[rp.external_id][room_type_external_id].append({})
            _logger.info("==[ODOO->CHANNEL]==== UPDATING RESTRICTIONS ==")
            _logger.info(restrictions)
            for k_res, v_res in restrictions.items():
                if any(v_res):
                    self.backend_adapter.update_rplan_values(
                        int(k_res),
                        date_start.strftime(DEFAULT_SERVER_DATE_FORMAT),
                        v_res)
            unpushed.with_context({
                'wubook_action': False}).write({'channel_pushed': True})
        return True
