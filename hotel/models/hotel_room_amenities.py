# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _


class HotelRoomAmenities(models.Model):
    _name = 'hotel.room.amenities'
    _description = 'Room amenities'
    
    # The record's name
    name = fields.Char('Amenity Name', required=True)
    # Used for activate records
    active = fields.Boolean('Active', default=True)

    default_code = fields.Char('Internal Reference', store=True)

    # room_categ_id = fields.Many2one('product.product', 'Product Category',
    #                                 required=True, delegate=True,
    #                                 ondelete='cascade')
    room_amenities_type_id = fields.Many2one('hotel.room.amenities.type',
                                             'Amenity Catagory')

    # room_ids = fields.Many2man('hotel.room','Rooms')

    # @api.multi
    # def unlink(self):
    #     # self.room_categ_id.unlink()
    #     return super(HotelRoomAmenities, self).unlink()
