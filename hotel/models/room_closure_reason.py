# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _


class RoomClosureReason(models.Model):
    _name = "room.closure.reason"
    _description = "Cause of out of service"

    name = fields.Char('Name', required=True)
    description = fields.Text('Description')
