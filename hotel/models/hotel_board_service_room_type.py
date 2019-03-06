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

    @api.multi
    def name_get(self):
        result = []
        for res in self:
            if res.pricelist_id:
                name = u'%s (%s)' % (res.hotel_board_service_id.name, res.pricelist_id.name)
            else:
                name = u'%s (%s)' % (res.hotel_board_service_id.name, _('Generic'))
            result.append((res.id, name))
        return result

    hotel_board_service_id = fields.Many2one(
        'hotel.board.service', 'Board Service', index=True, ondelete='cascade', required=True)
    hotel_room_type_id = fields.Many2one(
        'hotel.room.type', 'Room Type', index=True, ondelete='cascade', required=True)
    pricelist_id = fields.Many2one(
        'product.pricelist', 'Pricelist', required=False)
    price_type = fields.Selection([
        ('fixed', 'Fixed'),
        ('percent', 'Percent')], string='Type', default='fixed', required=True)
    amount = fields.Float('Amount',
                          digits=dp.get_precision('Product Price'),
                          compute='_compute_board_amount',
                          store=True)
    board_service_line_ids = fields.One2many('hotel.board.service.room.type.line', 'hotel_board_service_room_type_id')

    @api.model_cr
    def init(self):
        self._cr.execute('SELECT indexname FROM pg_indexes WHERE indexname = %s', ('hotel_board_service_id_hotel_room_type_id_pricelist_id',))
        if not self._cr.fetchone():
            self._cr.execute('CREATE INDEX hotel_board_service_id_hotel_room_type_id_pricelist_id ON hotel_board_service_room_type_rel (hotel_board_service_id, hotel_room_type_id, pricelist_id)')

    @api.model
    def create(self, vals):
        if 'hotel_board_service_id' in vals:
            vals.update(
                    self.prepare_board_service_room_lines(vals['hotel_board_service_id'])
                )
        return super(HotelBoardServiceRoomType, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'hotel_board_service_id' in vals:
            vals.update(
                    self.prepare_board_service_room_lines(vals['hotel_board_service_id'])
                )
        return super(HotelBoardServiceRoomType, self).write(vals)

    @api.multi
    def open_board_lines_form(self):
        action = self.env.ref('hotel.action_hotel_board_service_room_type_view').read()[0]
        action['views'] = [(self.env.ref('hotel.hotel_board_service_room_type_form').id, 'form')]
        action['res_id'] = self.id
        action['target'] = 'new'
        return action

    @api.depends('board_service_line_ids.amount')
    def _compute_board_amount(self):
        for record in self:
            total = 0
            for service in record.board_service_line_ids:
                total += service.amount
            record.update({'amount': total})

    @api.model
    def prepare_board_service_room_lines(self, board_service_id):
        """
        Prepare line to price products config
        """
        cmds=[(5,0,0)]
        board_service = self.env['hotel.board.service'].browse(board_service_id)
        for line in board_service.board_service_line_ids:
                cmds.append((0, False, {
                    'product_id': line.product_id.id,
                    'amount': line.amount
                }))
        return {'board_service_line_ids': cmds}

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
