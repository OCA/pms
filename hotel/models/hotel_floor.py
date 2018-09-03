# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _


class HotelFloor(models.Model):
    _name = "hotel.floor"
    _description = "Ubication"

    name = fields.Char('Ubication Name', size=64, required=True, index=True)
    sequence = fields.Integer('Sequence', size=64)
