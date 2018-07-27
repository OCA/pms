# -*- coding: utf-8 -*-
# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

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

    @api.constrains('capacity')
    def _check_capacity(self):
        if self.capacity < 1:
            raise ValidationError(_("Room capacity can't be less than one"))
