# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class HotelRoomTypeRestriction(models.Model):
    _name = 'hotel.room.type.restriction'

    @api.model
    def _get_default_hotel(self):
        return self.env.user.hotel_id

    name = fields.Char('Restriction Plan Name', required=True)
    item_ids = fields.One2many('hotel.room.type.restriction.item',
                               'restriction_id', string='Restriction Items',
                               copy=True)
    active = fields.Boolean('Active',
                            help='If unchecked, it will allow you to hide the \
                                    restriction plan without removing it.',
                            default=True)
    hotel_id = fields.Many2one('hotel.property', default=_get_default_hotel,
                               required=True, ondelete='cascade')

    @api.multi
    @api.depends('name')
    def name_get(self):
        restriction_id = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_restriction_id')
        if restriction_id:
            restriction_id = int(restriction_id)
        names = []
        for record in self:
            if record.id == restriction_id:
                names.append((record.id, '%s (Default)' % record.name))
            else:
                names.append((record.id, record.name))
        return names
