# Copyright 2019 Jose Luis Algara (Alda hotels) <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from datetime import datetime, timedelta
import logging
import random

class HotelReservation(models.Model):

    _inherit = 'hotel.reservation'

    def _compute_localizator(self):
        random.seed(self.id)
        number = str(random.random())
        leters = "ABCEFGHJKL"
        locali = str(self.folio_id.id) + leters[int(number[11])]
        locali += number[2:10] + leters[int(number[12])]
        locali += str(self.id)
        self.localizator = locali
        return

    localizator = fields.Char('Localizator', compute='_compute_localizator')
