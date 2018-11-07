# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class HotelRoomAmenitieType(models.Model):
    _name = 'hotel.room.amenitie.type'
    _description = 'Amenities Type'

    name = fields.Char('Amenity Name', required=True)
    active = fields.Boolean('Active', default=True)
    room_amenitie_ids = fields.One2many('hotel.room.amenitie',
                                         'room_amenitie_type_id',
                                         'Amenities in this category')
