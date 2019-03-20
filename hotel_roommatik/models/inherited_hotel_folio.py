# Copyright 2018 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from odoo import api, models


class HotelFolio(models.Model):

    _inherit = 'hotel.folio'

    @api.model
    def rm_get_reservation(self, Code):
        # BÚSQUEDA DE RESERVA POR LOCALIZADOR
        folio_res = self.env['hotel.folio'].search([('id', '=', Code)])
        json_response = dict()
        if any(folio_res):
            folio_lin = folio_res.room_lines
            json_response = {
                'Id': folio_res.id,
                'Arrival': folio_lin[0]['checkin'],
                'Departure': folio_lin[0]['checkout'],
                'Deposit': folio_res.amount_total,
            }
            for i, line in enumerate(folio_lin):
                json_response.setdefault('Rooms', [i]).append({
                    'Id': line.id,
                    'Adults': line.adults,
                    # Need a function (Clean and no Checkin)
                    'IsAvailable': 0,
                    'Price': line.price_total,
                    'RoomTypeId': line.room_type_id.id,
                    'RoomTypeName': line.room_type_id.name,
                    'RoomName': line.room_id.name,
                })
        json_response = json.dumps(json_response)

        return json_response
