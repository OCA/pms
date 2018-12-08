# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class HotelBoardServiceRoomType(models.Model):
    _name = 'hotel.board.service.room.type'
    _table = 'hotel_board_service_room_type_rel'
    _rec_name = 'hotel_board_service_id'
    _log_access = False
    _description = 'Board Service included in Room'

    hotel_board_service_id = fields.Many2one(
        'hotel.board.service', 'Board Service', index=True, ondelete='cascade', required=True)
    hotel_room_type_id = fields.Many2one(
        'hotel.room.type', 'Room Type', index=True, ondelete='cascade', required=True)
    pricelist_id = fields.Many2one(
        'product.pricelist', 'Pricelist', required=False)
    price_type = fields.Selection([
        ('fixed','Fixed'),
        ('percent','Percent')], string='Type', default='fixed', required=True)
    amount = fields.Float('Amount', digits=dp.get_precision('Product Price'), default=0.0)
    
    @api.model_cr
    def init(self):
        self._cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = %s', ('hotel_board_service_id_hotel_room_type_id_pricelist_id',))
        if not self._cr.fetchone():
            self._cr.execute('CREATE INDEX hotel_board_service_id_hotel_room_type_id_pricelist_id ON hotel_board_service_room_type_rel (hotel_board_service_id, hotel_room_type_id, pricelist_id)')

    @api.constrains('pricelist_id')
    def constrains_pricelist_id(self):
        for record in self:
            if self.pricelist_id:
                board_pricelist = self.env['hotel.board.service.room.type'].search([
                    ('pricelist_id','=', record.pricelist_id.id),
                    ('hotel_room_type_id','=', record.hotel_room_type_id.id),
                    ('hotel_board_service_id','=',record.hotel_board_service_id.id),
                    ('id','!=',record.id)
                ])
                if board_pricelist:
                    raise UserError(
                        _("This Board Service in this Room can't repeat pricelist"))
            else:
                board_pricelist = self.env['hotel.board.service.room.type'].search([
                    ('pricelist_id','=', False),
                    ('hotel_room_type_id','=', record.hotel_room_type_id.id),
                    ('hotel_board_service_id','=',record.hotel_board_service_id.id),
                    ('id','!=',record.id)
                ])
                if board_pricelist:
                    raise UserError(
                        _("This Board Service in this Room can't repeat without pricelist"))
                
                    
