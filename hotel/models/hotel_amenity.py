# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields

class HotelRoomAmenitie(models.Model):
    _name = 'hotel.amenity'
    _description = 'Room amenities'

    name = fields.Char('Amenity Name', translate=True, required=True)
    active = fields.Boolean('Active', default=True)
    default_code = fields.Char('Internal Reference')
    room_amenity_type_id = fields.Many2one('hotel.amenity.type',
                                             'Amenity Catagory')
