# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _


class HotelBoardService(models.Model):
    _name = "hotel.board.service"
    _description = "Board Services"

    name = fields.Char('Board Name', size=64, required=True, index=True)
    service_ids = fields.Many2many(comodel_name='product.template',
                                      relation='board_services_room',
                                      column1='board_id',
                                      column2='service_id')
    sequence = fields.Integer('Sequence', size=64)
