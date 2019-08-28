# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class HotelRoomAmenitieType(models.Model):
    _name = 'hotel.amenity.type'
    _description = 'Amenities Type'

    name = fields.Char('Amenity Name', translate=True, required=True)
    active = fields.Boolean('Active', default=True)
    room_amenity_ids = fields.One2many('hotel.amenity',
                                       'room_amenity_type_id',
                                       'Amenities in this category')
    hotel_ids = fields.Many2many('hotel.property', string='Hotels', required=False, ondelete='restrict')

    #TODO: Constrain coherence hotel_ids with amenities hotel_ids
