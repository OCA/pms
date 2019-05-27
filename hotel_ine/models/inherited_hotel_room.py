# Copyright 2019 Jose Luis Algara <osotranquilo@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class HotelRoom(models.Model):
    _inherit = 'hotel.room'

    in_ine = fields.Boolean('Included in the INE statistics', default=True)
