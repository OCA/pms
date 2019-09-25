# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class HotelRoomTypeRestriction(models.Model):
    """ The hotel room type restriction is used as a daily restriction plan for room types
     and therefore is related only with one hotel. """
    _name = 'hotel.room.type.restriction'

    # Default methods
    @api.model
    def _get_default_hotel(self):
        return self.env.user.hotel_id or None

    # Fields declaration
    name = fields.Char('Restriction Plan Name', required=True)
    hotel_id = fields.Many2one('hotel.property', 'Hotel', ondelete='restrict',
                               default=_get_default_hotel)
    item_ids = fields.One2many('hotel.room.type.restriction.item',
                               'restriction_id', string='Restriction Items',
                               copy=True)
    active = fields.Boolean('Active', default=True,
                            help='If unchecked, it will allow you to hide the '
                                 'restriction plan without removing it.')
