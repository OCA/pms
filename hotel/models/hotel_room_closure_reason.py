# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields

class RoomClosureReason(models.Model):
    _name = "room.closure.reason"
    _description = "Cause of out of service"

    name = fields.Char('Name', translate=True, required=True)
    description = fields.Text('Description', translate=True)
    hotel_ids = fields.Many2many('hotel.property', string='Hotels', required=False,
                                 ondelete='restrict')
