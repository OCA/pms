# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class HotelBoardServiceLine(models.Model):
    _name = 'hotel.board.service.line'
    _description = 'Services on Board Service included'

    def _get_default_price(self):
        if self.product_id:
            return self.product_id.list_price

    hotel_board_service_id = fields.Many2one(
        'hotel.board.service',
        'Board Service',
        ondelete='cascade',
        required=True)
    product_id = fields.Many2one(
        'product.product', 'Product', required=True)
    amount = fields.Float(
        'Amount',
        digits=dp.get_precision('Product Price'),
        default=_get_default_price)

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.update({'amount': self.product_id.list_price})
