# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models, fields
from odoo.addons import decimal_precision as dp


class HotelBoardService(models.Model):
    _name = "hotel.board.service"
    _description = "Board Services"

    name = fields.Char('Board Name', translate=True, size=64, required=True, index=True)
    board_service_line_ids = fields.One2many('hotel.board.service.line',
                                             'hotel_board_service_id')
    price_type = fields.Selection([
        ('fixed','Fixed'),
        ('percent','Percent')], string='Type', default='fixed', required=True)
    hotel_board_service_room_type_ids = fields.One2many(
        'hotel.board.service.room.type', 'hotel_board_service_id')
    amount = fields.Float('Amount',
                          digits=dp.get_precision('Product Price'),
                          compute='_compute_board_amount',
                          store=True)

    @api.depends('board_service_line_ids.amount')
    def _compute_board_amount(self):
        for record in self:
            total = 0
            for service in record.board_service_line_ids:
                total += service.amount
            record.update({'amount': total})
