# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class HotelRoomTypeRestriction(models.Model):
    _name = 'hotel.room.type.restriction'

    name = fields.Char('Restriction Plan Name', required=True)
    item_ids = fields.One2many('hotel.room.type.restriction.item',
                               'restriction_id', string='Restriction Items',
                               copy=True)
    active = fields.Boolean('Active', default=True,
                            help='If unchecked, it will allow you to hide the '
                                 'restriction plan without removing it.')