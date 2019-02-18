# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class HotelRoom(models.Model):
    _inherit = 'hotel.room'

    # hcal_sequence = fields.Integer('Calendar Sequence', default=0)
