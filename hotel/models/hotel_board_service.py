# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class HotelBoardService(models.Model):
    _name = "hotel.board.service"
    _description = "Board Services"

    name = fields.Char('Board Name', size=64, required=True, index=True)
    service_ids = fields.Many2many(comodel_name='product.product',
                                   relation='hotel_board_services_reservation',
                                   column1='board_id',
                                   column2='service_id')
    sequence = fields.Integer('Sequence')
