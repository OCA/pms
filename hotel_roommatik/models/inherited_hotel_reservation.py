# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
from datetime import datetime, timedelta
from dateutil import tz
import json
import logging
_logger = logging.getLogger(__name__)
import random


class HotelReservation(models.Model):

    _inherit = 'hotel.reservation'

    @api.model
    def rm_get_reservation(self, code):
        # BÚSQUEDA DE RESERVA POR LOCALIZADOR
        reservations = self._get_reservations_roommatik(code)
        reservations = reservations.filtered(
            lambda x: x.state in ('draft', 'confirm'))
        if any(reservations):
            default_arrival_hour = self.env['ir.default'].sudo().get(
                'res.config.settings', 'default_arrival_hour')
            checkin = "%s %s" % (reservations[0].checkin,
                                 default_arrival_hour)
            default_departure_hour = self.env['ir.default'].sudo().get(
                'res.config.settings', 'default_departure_hour')
            checkout = "%s %s" % (reservations[0].checkout,
                                  default_departure_hour)
            _logger.info('ROOMMATIK serving  Folio: %s', reservations.ids)
            json_response = {
                'Reservation': {
                    'Id': reservations[0].localizator,
                    'Arrival': checkin,
                    'Departure': checkout,
                    'Deposit': reservations[0].folio_id.invoices_paid,
                }
            }
            for i, line in enumerate(reservations):
                total_chekins = line.checkin_partner_pending_count
                json_response['Reservation'].setdefault('Rooms', [i]).append({
                    'Id': line.id,
                    'Adults': line.adults,
                    'IsAvailable': total_chekins > 0,
                    # IsAvailable “false” Rooms not need check-in
                    'Price': line.price_total,
                    'RoomTypeId': line.room_type_id.id,
                    'RoomTypeName': line.room_type_id.name,
                    'RoomName': line.room_id.name,
                })
        else:
            _logger.warning('ROOMMATIK Not Found reservation search  %s', code)
            json_response = {'Error': 'Not Found ' + str(code)}
        return json.dumps(json_response)

    @api.model
    def _get_reservations_roommatik(self, code):
        return self.env['hotel.reservation'].search([
            '|', ('localizator', '=', code),
            ('folio_id.name', '=', code)])
