# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from odoo import api, models
import logging
_logger = logging.getLogger(__name__)


class HotelFolio(models.Model):

    _inherit = 'hotel.folio'

    @api.model
    def rm_get_reservation(self, Code):
        # BÚSQUEDA DE RESERVA POR LOCALIZADOR
        folio_res = self.env['hotel.folio'].search([('id', '=', Code)])
        if any(folio_res):
            _logger.info('ROOMMATIK serving  Folio: %s', folio_res.id)
            folio_lin = folio_res.room_lines
            json_response = {
                'Id': folio_res.id,
                'Arrival': folio_lin[0]['checkin'],
                'Departure': folio_lin[0]['checkout'],
                'Deposit': folio_res.amount_total,
            }
            for i, line in enumerate(folio_lin):
                total_chekins = folio_lin.checkin_partner_pending_count
                json_response.setdefault('Rooms', [i]).append({
                    'Id': line.id,
                    'Adults': line.adults,
                    'IsAvailable': True if total_chekins > 0 else False,
                    # IsAvailable “false” Rooms not need check-in
                    'Price': line.price_total,
                    'RoomTypeId': line.room_type_id.id,
                    'RoomTypeName': line.room_type_id.name,
                    'RoomName': line.room_id.name,
                })
            # Debug Stop -------------------
            # import wdb; wdb.set_trace()
            # Debug Stop -------------------
        else:
            _logger.warning('ROOMMATIK Not Found Folio search  %s', Code)
            json_response = {'Error': 'Not Found ' + str(Code)}
        return json.dumps(json_response)
