# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _


class HotelRoomAmenitiesType(models.Model):
    _name = 'hotel.room.amenities.type'
    _description = 'Amenities Type'
    # The record's name
    name = fields.Char('Amenity Name', required=True)
    # Used for activate records
    active = fields.Boolean('Active', default=True)

    room_amenities_ids = fields.One2many('hotel.room.amenities',
                                         'room_amenities_type_id',
                                         'Amenities in this category')

    # cat_id = fields.Many2one('product.category', 'category', required=True,
    #                          delegate=True, ondelete='cascade')

    # @api.multi
    # def unlink(self):
    #     # self.cat_id.unlink()
    #     return super(HotelRoomAmenitiesType, self).unlink()
