# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class HotelFloor(models.Model):
    _name = "hotel.floor"
    _description = "Ubication"

    name = fields.Char('Ubication Name', translate=True, size=64, required=True, index=True)
    sequence = fields.Integer('Sequence')
