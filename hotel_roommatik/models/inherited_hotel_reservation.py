# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.addons.hotel_roommatik.models.roommatik import (
    DEFAULT_ROOMMATIK_DATE_FORMAT,
    DEFAULT_ROOMMATIK_DATETIME_FORMAT)
from datetime import datetime, timedelta
from dateutil import tz
import json
import logging
_logger = logging.getLogger(__name__)

class HotelReservation(models.Model):

    _inherit = 'hotel.reservation'

    @api.model
    def _computed_deposit_roommatik(self, rm_localizator):
        reservations = self.env['hotel.reservation'].search([
            ('localizator', '=', rm_localizator)])
        folio = reservations[0].folio_id
        # We dont have the payments by room, that's why we have to computed
        # the proportional deposit part if the folio has more rooms that the
        # reservations code (this happens when in the same folio are
        # reservations with different checkins/outs convinations)
        if len(folio.room_lines) > len(reservations) and folio.invoices_paid > 0:

            total_reservations = sum(reservations.mapped('price_total'))
            paid_in_folio = folio.invoices_paid
            total_in_folio = folio.amount_total
            deposit = total_reservations * paid_in_folio / total_in_folio
            return deposit
        return folio.invoices_paid


    @api.model
    def rm_get_reservation(self, code):
        # Search by localizator
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
                    'Deposit': self._computed_deposit_roommatik(code)
                }
            }
            for i, line in enumerate(reservations):
                total_chekins = line.checkin_partner_pending_count
                json_response['Reservation'].setdefault('Rooms', []).append({
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
