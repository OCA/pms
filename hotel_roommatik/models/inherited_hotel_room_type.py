# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from datetime import datetime, timedelta
import logging


class HotelRoomType(models.Model):

    _inherit = "hotel.room.type"

    @api.model
    def rm_get_all_room_type_rates(self):
        # types = self.env['hotel.room.type'].search(['active', '=', True])
        types = self.env['hotel.room.type'].search([])
        dfrom = datetime.now()
        dto = (dfrom + timedelta(hours=24))

        room_type_rates = []
        for i, type in enumerate(types):
            frees = self.check_availability_room_type(dfrom, dto, type.id)
            if any(frees):
                room_type_rates.append({
                    "RoomType": {
                        "Id": type.id,
                        "Name": type.product_id.name,
                        "GuestNumber": type.get_capacity()
                        },
                    "TimeInterval": {
                        "Id": "1",
                        "Name": "1 day",
                        "Minutes": "1440"
                        },
                    "Price": "",
                    "IsAvailable": "",
                })

        return room_type_rates

    @api.model
    def rm_get_prices(self, start_date, time_interval, number_intervals, room_type, guest_number):
        # TODO: FALTA POR COMPLETO
        _logger = logging.getLogger(__name__)
        _logger.info('ROOMMATIK get prices date %s Room: %s for %s Guests',
                     start_date,
                     room_type,
                     guest_number)
        return {'start_date': start_date, 'time_interval': time_interval, 'number_intervals': number_intervals}
