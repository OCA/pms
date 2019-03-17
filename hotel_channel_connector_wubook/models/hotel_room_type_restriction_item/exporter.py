# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta
from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import api,fields
_logger = logging.getLogger(__name__)


class HotelRoomTypeRestrictionItemExporter(Component):
    _inherit = 'channel.hotel.room.type.restriction.item.exporter'

    @api.model
    def push_restriction(self):
        channel_hotel_room_type_obj = self.env['channel.hotel.room.type']
        channel_room_type_rest_obj = self.env['channel.hotel.room.type.restriction']
        channel_rest_item_obj = self.env['channel.hotel.room.type.restriction.item']
        unpushed = channel_rest_item_obj.search([
            ('backend_id', '=', self.backend_record.id),
            ('channel_pushed', '=', False),
            ('date', '>=', fields.Date.today())
        ], order="date ASC")
        if any(unpushed):
            date_start = fields.Date.from_string(unpushed[0].date)
            date_end = fields.Date.from_string(unpushed[-1].date)
            days_diff = (date_end-date_start).days + 1
            restrictions = {}
            channel_restr_plan_ids = channel_room_type_rest_obj.search([
                ('backend_id', '=', self.backend_record.id),
            ])
            for rp in channel_restr_plan_ids:
                restrictions.update({rp.external_id: {}})
                unpushed_rp = channel_rest_item_obj.search([
                    ('backend_id', '=', self.backend_record.id),
                    ('channel_pushed', '=', False),
                    ('restriction_id', '=', rp.odoo_id.id)
                ])
                room_type_ids = unpushed_rp.mapped('room_type_id')
                for room_type in room_type_ids:
                    if any(room_type.channel_bind_ids):
                        room_type_bind = channel_hotel_room_type_obj.search([
                            ('odoo_id', '=', room_type.id),
                            ('backend_id', '=', self.backend_record.id),
                        ], limit=1)
                        room_type_external_id = room_type_bind.external_id
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
            _logger.info("==[ODOO->CHANNEL]==== RESTRICTIONS ==")
            _logger.info(restrictions)
            try:
                for k_res, v_res in restrictions.items():
                    if any(v_res):
                        self.backend_adapter.update_rplan_values(
                            int(k_res),
                            date_start.strftime(DEFAULT_SERVER_DATE_FORMAT),
                            v_res)
            except ChannelConnectorError as err:
                self.create_issue(
                    section='restriction',
                    internal_message=str(err),
                    channel_message=err.data['message'])
            else:
                unpushed.with_context({
                    'connector_no_export': True,
                }).write({
                    'channel_pushed': True,
                    'sync_date': fields.Datetime.now(),
                })
        return True

    @api.model
    def close_online_sales(self):
        channel_rest_plan = self.env['channel.hotel.room.type.restriction'].search([
            ('backend_id', '=', self.backend_record.id),
        ])
        channel_rest_item = self.env['channel.hotel.room.type.restriction.item']
        channel_room_types = self.env['channel.hotel.room.type'].search([
            ('external_id', '!=', ''),
        ])
        for channel_room_type in channel_room_types:
            today_restrictions = channel_rest_item.search([
                ('backend_id', '=', self.backend_record.id),
                ('room_type_id', '=', channel_room_type.odoo_id.id),
                ('date', '=', fields.Date.today())
            ])
            if today_restrictions:
                today_restrictions.closed = True
            else:
                self.env['hotel.room.type.restriction.item'].with_context(
                        {'connector_no_export': True}
                    ).create({
                        'restriction_id': channel_rest_plan.odoo_id.id,
                        'room_type_id': channel_room_type.odoo_id.id,
                        'date': fields.Date.today(),
                        'closed_departure': 0,
                        'max_stay_arrival': 0,
                        'min_stay': 0,
                        'max_stay': 0,
                        'min_stay_arrival': 0,
                        'closed_arrival': 0,
                        'closed': True,
                        'channel_bind_ids': [(0, False, {
                            'channel_pushed': False,
                            'backend_id': self.backend_record.id,
                        })]
                    })

        return self.push_restriction()
