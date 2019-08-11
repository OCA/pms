# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from datetime import datetime, timedelta
import json
from odoo.addons.hotel_roommatik.models.roommatik import (
    DEFAULT_ROOMMATIK_DATE_FORMAT,)
import logging
_logger = logging.getLogger(__name__)


class HotelRoomType(models.Model):

    _inherit = "hotel.room.type"

    @api.model
    def rm_get_all_room_type_rates(self):
        room_types = self.env['hotel.room.type'].search([])
        tz_hotel = self.env['ir.default'].sudo().get(
            'res.config.settings', 'tz_hotel')
        dfrom = fields.Date.context_today(self.with_context(
            tz=tz_hotel))
        dto = (fields.Date.from_string(dfrom) + timedelta(days=1)).strftime(
            DEFAULT_ROOMMATIK_DATE_FORMAT)
        room_type_rates = []
        for room_type in room_types:
            free_rooms = self.check_availability_room_type(dfrom, dto,
                                                           room_type.id)
            rates = self.get_rate_room_types(
                room_type_ids=room_type.id,
                date_from=dfrom,
                days=1,
                partner_id=False)
            room_type_rates.append({
                "RoomType": {
                    "Id": room_type.id,
                    "Name": room_type.name,
                    "GuestNumber": room_type.get_capacity()
                    },
                "TimeInterval": {
                    "Id": "1",
                    "Name": "1 day",
                    "Minutes": "1440"
                    },
                "Price": rates[room_type.id][0].get('price'),
                "IsAvailable": any(free_rooms),
            })
            json_response = json.dumps(room_type_rates)
        return json_response

    @api.model
    def rm_get_prices(self, start_date, number_intervals,
                      room_type, guest_number):
        start_date = fields.Date.from_string(start_date)
        end_date = start_date + timedelta(days=int(number_intervals))
        dfrom = start_date.strftime(
            DEFAULT_ROOMMATIK_DATE_FORMAT)
        dto = end_date.strftime(
            DEFAULT_ROOMMATIK_DATE_FORMAT)
        free_rooms = self.check_availability_room_type(dfrom, dto,
                                                       room_type.id)
        if free_rooms:
            rates = self.get_rate_room_types(
                room_type_ids=room_type.id,
                date_from=dfrom,
                days=int(number_intervals),
                partner_id=False)
            return [item['price'] for item in rates.get(room_type.id)]
        return []
