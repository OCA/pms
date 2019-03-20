# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from datetime import datetime
from odoo import api, models


class RoomMatik(models.Model):
    _name = 'roommatik.api'

    @api.model
    def rm_get_date(self):
        # FECHA/HORA
        # Need know UTC in the machine/hotel
        utc_s = '+01:00'
        json_response = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f") + utc_s
        json_response = json.dumps(json_response)
        return json_response

        # Debug Stop -------------------
        # import wdb; wdb.set_trace()
        # Debug Stop -------------------
