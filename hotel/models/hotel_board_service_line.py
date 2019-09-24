# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class HotelBoardServiceLine(models.Model):
    _name = 'hotel.board.service.line'
    _description = 'Services on Board Service included'

    # Default methods
    def _get_default_price(self):
        if self.product_id:
            return self.product_id.list_price

    # Fields declaration
    hotel_board_service_id = fields.Many2one(
        'hotel.board.service',
        'Board Service',
        ondelete='cascade',
        required=True)
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True)
    hotel_ids = fields.Many2many(
        'hotel.property',
        related='hotel_board_service_id.hotel_ids')
    amount = fields.Float(
        'Amount',
        digits=dp.get_precision('Product Price'),
        default=_get_default_price)

    # Constraints and onchanges
    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.update({'amount': self.product_id.list_price})
