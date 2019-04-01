# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from datetime import datetime
from odoo import api, models


class RoomMatik(models.Model):
    _name = 'roommatik.api'

    @api.model
    def rm_get_date(self):
        # RoomMatik API FECHA/HORA
        utc_s = '+01:00'
        # TODO Need know UTC in the machine/hotel
        json_response = {
            'dateTime': datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f") + utc_s
            }
        json_response = json.dumps(json_response)
        return json_response

    @api.model
    def rm_add_customer(self, customer):
        # RoomMatik API CREACIÓN DE CLIENTE
        apidata = self.env['res.partner']
        return apidata.rm_add_customer(customer)

    @api.model
    def rm_checkin_partner(self, stay):
        # RoomMatik API CHECK-IN
        apidata = self.env['hotel.folio']
        return apidata.rm_checkin_partner(stay)

        # Debug Stop -------------------
        # import wdb; wdb.set_trace()
        # Debug Stop -------------------
