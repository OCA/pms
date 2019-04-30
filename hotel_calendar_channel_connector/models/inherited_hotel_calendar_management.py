# Copyright 2019 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import timedelta
from odoo import models, api, fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class HotelCalendarManagement(models.TransientModel):
    _inherit = 'hotel.calendar.management'

    @api.model
    def _hcalendar_availability_json_data(self, dfrom, dto):
        date_start = fields.Date.from_string(dfrom)
        date_end = fields.Date.from_string(dto)
        date_diff = abs((date_end - date_start).days) + 1
        hotel_room_type_avail_obj = self.env['hotel.room.type.availability']
        room_types = self.env['hotel.room.type'].search([])
        json_data = {}

        for room_type in room_types:
            json_data[room_type.id] = []
            for i in range(0, date_diff):
                cur_date = date_start + timedelta(days=i)
                cur_date_str = cur_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                avail = hotel_room_type_avail_obj.search([
                    ('date', '=', cur_date_str),
                    ('room_type_id', '=', room_type.id)
                ])
                json_data[room_type.id].append(
                    self._generate_avalaibility_data(room_type, cur_date_str, avail))
        return json_data

    @api.model
    def _generate_avalaibility_data(self, room_type, date, avail):
        avalaibility_data = {
            'id': False,
            'date': date,
            'no_ota': False,
            'quota': room_type.channel_bind_ids.default_quota,
            'max_avail': room_type.channel_bind_ids.default_max_avail,
            'channel_avail': room_type.channel_bind_ids.default_availability
        }
        if avail:
            avalaibility_data = {
                'id': avail.id,
                'date': avail.date,
                'no_ota': avail.no_ota,
                'quota': avail.quota,
                'max_avail': avail.max_avail,
                'channel_avail': avail.channel_bind_ids.channel_avail
            }
        return avalaibility_data

    @api.model
    def _get_availability_values(self, vals):
        vals = {
            'quota': vals['quota'],
            'max_avail': vals['max_avail'],
            'no_ota': vals['no_ota'],
        }
        return vals

    @api.multi
    def save_changes(self, pricelist_id, restriction_id, pricelist,
                     restrictions, availability={}):
        res = super(HotelCalendarManagement, self).save_changes(
            pricelist_id,
            restriction_id,
            pricelist,
            restrictions,
            availability=availability)

        room_type_obj = self.env['hotel.room.type']
        room_type_avail_obj = self.env['hotel.room.type.availability']
        # Save Availability
        for k_avail in availability.keys():
            room_type_id = room_type_obj.browse(int(k_avail))
            for avail in availability[k_avail]:
                vals = self._get_availability_values(avail)
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

        self.env['channel.backend'].cron_push_changes()
        return res

    @api.model
    def get_hcalendar_all_data(self, dfrom, dto, pricelist_id, restriction_id,
                               withRooms):
        res = super(HotelCalendarManagement, self).get_hcalendar_all_data(
            dfrom, dto, pricelist_id, restriction_id, withRooms)
        json_avails = self._hcalendar_availability_json_data(dfrom, dto)
        res.update({
            'availability': json_avails or [],
        })
        return res
