# -*- coding: utf-8 -*-
# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _


class HotelRoom(models.Model):
    """ The rooms for lodging can be for sleeping, usually called rooms, and also
     for speeches (conference rooms), parking, relax with cafe con leche, spa...
     """
    _name = 'hotel.room'
    _description = 'Hotel Room'
    # The record's name
    name = fields.Char('Room Name', required=True)
    # Used for activate records
    active = fields.Boolean('Active', default=True)
    # Used for ordering
    sequence = fields.Integer('Sequence', default=0)

    _order = "sequence, room_type_id, name"

    # each room has only one type (Many2one)
    room_type_id = fields.Many2one('hotel.room.type', 'Hotel Room Type')

    floor_id = fields.Many2one('hotel.floor', 'Ubication',
                               help='At which floor the room is located.')
    # TODO Q. Should the amenities be on the Room Type ? -
    room_amenities = fields.Many2many('hotel.room.amenities', 'temp_tab',
                                      'room_amenities', 'rcateg_id',
                                      string='Room Amenities',
                                      help='List of room amenities.')

    # default price for this room
    list_price = fields.Float(store=True,
                              string='Room Rate',
                              help='The room rate is fixed unless a room type'
                              ' is selected, in which case the rate is taken from'
                              ' the room type.')
    # how to manage the price
    # sale_price_type = fields.Selection([
    #     ('fixed', 'Fixed Price'),
    #     ('vroom', 'Room Type'),
    # ], 'Price Type', default='fixed', required=True)
    # max number of adults and children per room
    max_adult = fields.Integer('Max Adult')
    max_child = fields.Integer('Max Child')
    # maximum capacity of the room
    capacity = fields.Integer('Capacity')
    # FIXME not used
    to_be_cleaned = fields.Boolean('To be Cleaned', default=False)

    shared_room = fields.Boolean('Shared Room', default=False)

    description_sale = fields.Text(
        'Sale Description', translate=True,
        help="A description of the Product that you want to communicate to "
             " your customers. This description will be copied to every Sales "
             " Order, Delivery Order and Customer Invoice/Credit Note")


    # In case the price is managed from a specific type of room
    # price_virtual_room = fields.Many2one(
    #     'hotel.virtual.room',
    #     'Price Virtual Room',
    #     help='Price will be based on selected Virtual Room')

    # virtual_rooms = fields.Many2many('hotel.virtual.room',
    #                                  string='Virtual Rooms')
    # categ_id = fields.Selection([('room', 'Room '),
    #                              ('shared_room', 'Shared Room'),
    #                              ('parking', 'Parking')],
    #                             string='Hotel Lodging Type',
    #                             store=True, default='room')

#     price_virtual_room_domain = fields.Char(
#         compute=_compute_price_virtual_room_domain,
#         readonly=True,
#         store=False,
#     )

#     @api.multi
#     @api.depends('categ_id')
#     def _compute_price_virtual_room_domain(self):
#         for rec in self:
#             rec.price_virtual_room_domain = json.dumps(
#                 ['|', ('room_ids.id', '=', rec.id), ('room_type_ids.cat_id.id', '=', rec.categ_id.id)]
#             )

    # @api.onchange('categ_id')
    # def price_virtual_room_domain(self):
        # return {
        #     'domain': {
        #         'price_virtual_room': [
        #             '|', ('room_ids.id', '=', self._origin.id),
        #                  ('room_type_ids.cat_id.id', '=', self.categ_id.id)
        #         ]
        #     }
        # }

    # @api.multi
    # def unlink(self):
    #     for record in self:
    #         record.product_id.unlink()
    #     return super(HotelRoom, self).unlink()
