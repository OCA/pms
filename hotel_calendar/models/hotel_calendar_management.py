# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from datetime import datetime, timedelta
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
from odoo import models, api, _, fields
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)


class HotelCalendarManagement(models.TransientModel):
    _name = 'hotel.calendar.management'

    @api.model
    def _get_prices_values(self, price):
        vals = {
            'fixed_price': price['price'],
        }
        return vals

    @api.model
    def _get_restrictions_values(self, restriction):
        vals = {
            'min_stay': restriction['min_stay'],
            'min_stay_arrival': restriction['min_stay_arrival'],
            'max_stay': restriction['max_stay'],
            'max_stay_arrival': restriction['max_stay_arrival'],
            'closed': restriction['closed'],
            'closed_arrival': restriction['closed_arrival'],
            'closed_departure': restriction['closed_departure'],
        }
        return vals

    @api.model
    def _get_availability_values(self, avail, room_type):
        room_type_obj = self.env['hotel.room.type']
        cavail = len(room_type_obj.check_availability_room(
            avail['date'], avail['date'], room_type_id=room_type.id))
        ravail = min(cavail, room_type.total_rooms_count, int(avail['avail']))
        vals = {
            'no_ota': avail['no_ota'],
            'avail': ravail,
        }
        return vals

    @api.model
    def save_changes(self, pricelist_id, restriction_id, pricelist,
                     restrictions, availability):
        room_type_obj = self.env['hotel.room.type']
        product_pricelist_item_obj = self.env['product.pricelist.item']
        room_type_rest_item_obj = self.env['hotel.room.type.restriction.item']
        room_type_avail_obj = self.env['hotel.room.type.availability']

        # Save Pricelist
        for k_price in pricelist.keys():
            room_type_id = room_type_obj.browse([int(k_price)])
            room_type_prod_tmpl_id = room_type_id.product_id.product_tmpl_id
            for price in pricelist[k_price]:
                price_id = product_pricelist_item_obj.search([
                    ('date_start', '>=', price['date']),
                    ('date_end', '<=', price['date']),
                    ('pricelist_id', '=', int(pricelist_id)),
                    ('applied_on', '=', '1_product'),
                    ('compute_price', '=', 'fixed'),
                    ('product_tmpl_id', '=', room_type_prod_tmpl_id.id),
                ], limit=1)
                vals = self._get_prices_values(price)
                if not price_id:
                    vals.update({
                        'date_start': price['date'],
                        'date_end': price['date'],
                        'pricelist_id': int(pricelist_id),
                        'applied_on': '1_product',
                        'compute_price': 'fixed',
                        'product_tmpl_id': room_type_prod_tmpl_id.id,
                    })
                    price_id = product_pricelist_item_obj.create(vals)
                else:
                    price_id.write(vals)

        # Save Restrictions
        for k_res in restrictions.keys():
            for restriction in restrictions[k_res]:
                res_id = room_type_rest_item_obj.search([
                    ('date', '=', restriction['date']),
                    ('restriction_id', '=', int(restriction_id)),
                    ('applied_on', '=', '0_room_type'),
                    ('room_type_id', '=', int(k_res)),
                ], limit=1)
                vals = self._get_restrictions_values(restriction)
                if not res_id:
                    vals.update({
                        'date': restriction['date'],
                        'restriction_id': int(restriction_id),
                        'applied_on': '0_room_type',
                        'room_type_id': int(k_res),
                    })
                    res_id = room_type_rest_item_obj.create(vals)
                else:
                    res_id.write(vals)

        # Save Availability
        for k_avail in availability.keys():
            room_type_id = room_type_obj.browse(int(k_avail))
            for avail in availability[k_avail]:
                vals = self._get_availability_values(avail, room_type_id)
                avail_id = room_type_avail_obj.search([
                    ('date', '=', avail['date']),
                    ('room_type_id', '=', room_type_id.id),
                ], limit=1)
                if not avail_id:
                    vals.update({
                        'date': avail['date'],
                        'room_type_id': room_type_id.id,
                    })
                    avail_id = room_type_avail_obj.with_context({
                        'mail_create_nosubscribe': True,
                    }).create(vals)
                else:
                    avail_id.write(vals)

    @api.model
    def _hcalendar_room_json_data(self, rooms):
        json_data = []
        for room in rooms:
            json_data.append((
                room.id,
                room.name,
                room.get_capacity(),
                room.list_price,
                room.total_rooms_count,
            ))
        return json_data

    @api.model
    def _hcalendar_pricelist_json_data(self, prices):
        json_data = {}
        room_type_obj = self.env['hotel.room.type']
        for rec in prices:
            room_type_id = room_type_obj.search([
                ('product_id.product_tmpl_id', '=', rec.product_tmpl_id.id)
            ], limit=1)
            if not room_type_id:
                continue

            # TODO: date_end - date_start loop
            json_data.setdefault(room_type_id.id, []).append({
                'id': rec.id,
                'price': rec.fixed_price,
                'date': rec.date_start,
            })
        return json_data

    @api.model
    def _hcalendar_restriction_json_data(self, restrictions):
        json_data = {}
        for rec in restrictions:
            json_data.setdefault(rec.room_type_id.id, []).append({
                'id': rec.id,
                'date': rec.date,
                'min_stay': rec.min_stay,
                'min_stay_arrival': rec.min_stay_arrival,
                'max_stay': rec.max_stay,
                'max_stay_arrival': rec.max_stay_arrival,
                'closed': rec.closed,
                'closed_departure': rec.closed_departure,
                'closed_arrival': rec.closed_arrival,
            })
        return json_data

    @api.model
    def _hcalendar_availability_json_data(self, dfrom, dto):
        date_start = fields.Date.from_string(dfrom)
        date_end = fields.Date.from_string(dto)
        date_diff = abs((date_end - date_start).days) + 1
        room_types = self.env['hotel.room.type'].search([])
        json_data = {}

        for room_type in room_types:
            json_data[room_type.id] = []
            for i in range(0, date_diff):
                cur_date = date_start + timedelta(days=i)
                cur_date_str = cur_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                avail = self.env['hotel.room.type.availability'].search([
                    ('date', '=', cur_date_str),
                    ('room_type_id', '=', room_type.id)
                ])
                if avail:
                    json_data[room_type.id].append({
                        'id': avail.id,
                        'date': avail.date,
                        'avail': avail.avail,
                        'no_ota': avail.no_ota,
                    })
                else:
                    json_data[room_type.id].append({
                        'id': False,
                        'date': cur_date_str,
                        'avail': room_type.total_rooms_count,
                        'no_ota': False,
                    })
        return json_data

    @api.model
    def _hcalendar_events_json_data(self, dfrom, dto):
        date_start = fields.Date.from_string(dfrom) - timedelta(days=1)
        date_start_str = date_start.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        user_id = self.env['res.users'].browse(self.env.uid)
        domain = []
        if user_id.pms_allowed_events_tags:
            domain.append(('categ_ids', 'in', user_id.pms_allowed_events_tags))
        if user_id.pms_denied_events_tags:
            domain.append(
                ('categ_ids', 'not in', user_id.pms_denied_events_tags))
        events_raw = self.env['calendar.event'].search(domain)
        events_ll = self.env['calendar.event'].search([
            ('start', '<=', dto),
            ('stop', '>=', date_start_str)
        ])
        events_lr = self.env['calendar.event'].search([
            ('start', '>=', date_start_str),
            ('stop', '<=', dto)
        ])
        events = (events_ll | events_lr) & events_raw
        json_data = []
        for event in events:
            json_data.append([
                event.id,
                event.name,
                event.start,
                event.location,
            ])
        return json_data

    @api.model
    def _hcalendar_get_count_reservations_json_data(self, dfrom, dto):
        date_start = fields.Date.from_string(dfrom)
        date_end = fields.Date.from_string(dto)
        date_diff = abs((date_end - date_start).days) + 1
        room_type_obj = self.env['hotel.room.type']
        room_types = room_type_obj.search([])
        json_data = {}

        for room_type in room_types:
            for i in range(0, date_diff):
                cur_date = date_start + timedelta(days=i)
                cur_date_str = cur_date.strftime(DEFAULT_SERVER_DATE_FORMAT)

                json_data.setdefault(room_type.id, []).append({
                    'date': cur_date_str,
                    'num': len(
                        room_type_obj.check_availability_room(
                            cur_date_str,
                            cur_date_str,
                            room_type_id=room_type.id)),
                })

        return json_data

    @api.model
    def get_hcalendar_all_data(self, dfrom, dto, pricelist_id, restriction_id,
                               withRooms):
        if not dfrom or not dto:
            raise ValidationError(_('Input Error: No dates defined!'))
        vals = {}
        if not pricelist_id:
            pricelist_id = self.env['ir.default'].sudo().get(
                'res.config.settings', 'parity_pricelist_id')
        if not restriction_id:
            restriction_id = self.env['ir.default'].sudo().get(
                'res.config.settings', 'parity_restrictions_id')

        pricelist_id = int(pricelist_id)
        vals.update({'pricelist_id': pricelist_id})
        restriction_id = int(restriction_id)
        vals.update({'restriction_id': restriction_id})

        room_type_rest_it_obj = self.env['hotel.room.type.restriction.item']
        restriction_item_ids = room_type_rest_it_obj.search([
            ('date', '>=', dfrom), ('date', '<=', dto),
            ('restriction_id', '=', restriction_id),
            ('applied_on', '=', '0_room_type'),
        ])

        pricelist_item_ids = self.env['product.pricelist.item'].search([
            ('date_start', '>=', dfrom), ('date_end', '<=', dto),
            ('pricelist_id', '=', pricelist_id),
            ('applied_on', '=', '1_product'),
            ('compute_price', '=', 'fixed'),
        ])

        json_prices = self._hcalendar_pricelist_json_data(pricelist_item_ids)
        json_rest = self._hcalendar_restriction_json_data(restriction_item_ids)
        json_avails = self._hcalendar_availability_json_data(dfrom, dto)
        json_rc = self._hcalendar_get_count_reservations_json_data(dfrom, dto)
        json_events = self._hcalendar_events_json_data(dfrom, dto)
        vals.update({
            'prices': json_prices or [],
            'restrictions': json_rest or [],
            'availability': json_avails or [],
            'count_reservations': json_rc or [],
            'events': json_events or [],
        })

        if withRooms:
            room_ids = self.env['hotel.room.type'].search(
                [],
                order='hcal_sequence ASC')
            json_rooms = self._hcalendar_room_json_data(room_ids)
            vals.update({'rooms': json_rooms or []})

        return vals

    @api.multi
    def get_hcalendar_settings(self):
        user_id = self.env['res.users'].browse(self.env.uid)
        return {
            'eday_week': user_id.npms_end_day_week,
            'eday_week_offset': user_id.npms_end_day_week_offset,
            'days': user_id.npms_default_num_days,
            'show_notifications': user_id.pms_show_notifications,
            'show_num_rooms': user_id.pms_show_num_rooms,
        }
