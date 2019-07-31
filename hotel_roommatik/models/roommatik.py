# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from datetime import datetime
from odoo import api, models, fields
# from odoo.tools import (
#     DEFAULT_SERVER_DATE_FORMAT,
#     DEFAULT_SERVER_DATETIME_FORMAT)
import logging
_logger = logging.getLogger(__name__)

DEFAULT_ROOMMATIK_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_ROOMMATIK_TIME_FORMAT = "%H:%M:%S"
DEFAULT_ROOMMATIK_DATETIME_FORMAT = "%s %s" % (
    DEFAULT_ROOMMATIK_DATE_FORMAT,
    DEFAULT_ROOMMATIK_TIME_FORMAT)

class RoomMatik(models.Model):
    _name = 'roommatik.api'

    @api.model
    def rm_get_date(self):
        # RoomMatik API Gets the current business date/time. (MANDATORY)
        tz_hotel = self.env['ir.default'].sudo().get(
            'res.config.settings', 'tz_hotel')
        self_tz = self.with_context(tz=tz_hotel)
        mynow = fields.Datetime.context_timestamp(self_tz, datetime.now()).\
            strftime(DEFAULT_ROOMMATIK_DATETIME_FORMAT)
        json_response = {
            'dateTime': mynow
            }
        json_response = json.dumps(json_response)
        return json_response

    @api.model
    def rm_get_reservation(self, reservation_code):
        # RoomMatik Gets a reservation ready for check-in
        # through the provided code. (MANDATORY)
        apidata = self.env['hotel.reservation']
        return apidata.sudo().rm_get_reservation(reservation_code)

    @api.model
    def rm_add_customer(self, customer):
        # RoomMatik API Adds a new PMS customer through the provided parameters
        # Addition will be ok if the returned customer has ID. (MANDATORY)
        _logger.info('ROOMMATIK Customer Creation')
        apidata = self.env['res.partner']
        return apidata.sudo().rm_add_customer(customer)

    @api.model
    def rm_checkin_partner(self, stay):
        # RoomMatik API Check-in a stay.
        # Addition will be ok if the returned stay has ID. (MANDATORY)
        _logger.info('ROOMMATIK Check-IN')
        apidata = self.env['hotel.checkin.partner']
        return apidata.sudo().rm_checkin_partner(stay)

    @api.model
    def rm_get_stay(self, check_in_code):
        # RoomMatik API  Gets stay information through check-in code
        # (if code is related to a current stay)
        # (MANDATORY for check-out kiosk)
        apidata = self.env['hotel.checkin.partner']
        return apidata.sudo().rm_get_stay(check_in_code)

    @api.model
    def rm_get_all_room_type_rates(self):
        # Gets the current room rates and availability. (MANDATORY)
        # return ArrayOfRoomTypeRate
        _logger.info('ROOMMATIK Get Rooms and Rates')
        apidata = self.env['hotel.room.type']
        return apidata.sudo().rm_get_all_room_type_rates()

    @api.model
    def rm_get_prices(self, start_date, number_intervals, room_type, guest_number):
        # Gets some prices related to different dates of the same stay.
        # return ArrayOfDecimal
        room_type = self.env['hotel.room.type'].browse(room_type)
        _logger.info('ROOMMATIK Get Prices')
        apidata = self.env['hotel.room.type']
        return apidata.sudo().rm_get_prices(start_date, number_intervals, room_type, guest_number)

    @api.model
    def rm_get_segmentation(self):
        # Gets segmentation list
        # return ArrayOfSegmentation
        segmentations = self.env['res.partner.category'].sudo().search([])
        _logger.info('ROOMMATIK Get segmentation')
        response = []
        for segmentation in segmentations:
            response.append({
                "Segmentation": {
                    "Id": segmentation.id,
                    "Name": segmentation.display_name,
                    },
                })
            json_response = json.dumps(response)
        return json_response

    @api.model
    def _rm_add_payment(self, code, payment):
        apidata = self.env['account.payment']
        return apidata.sudo().rm_checkin_partner(code, payment)
        # Debug Stop -------------------
        # import wdb; wdb.set_trace()
        # Debug Stop -------------------
