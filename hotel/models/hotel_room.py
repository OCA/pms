# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# Copyright 2018  Pablo Quesada
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HotelRoom(models.Model):
    """ The rooms for lodging can be for sleeping, usually called rooms, and also
     for speeches (conference rooms), parking, relax with cafe con leche, spa...
     """
    _name = 'hotel.room'
    _description = 'Hotel Room'
    _order = "sequence, room_type_id, name"

    # Fields declaration
    name = fields.Char('Room Name', required=True)
    hotel_id = fields.Many2one('hotel.property', store=True, readonly=True,
                               related='room_type_id.hotel_id')
    room_type_id = fields.Many2one('hotel.room.type', 'Hotel Room Type',
                                   required=True,
                                   ondelete='restrict')
    shared_room_id = fields.Many2one('hotel.shared.room', 'Shared Room',
                                     default=False)
    floor_id = fields.Many2one('hotel.floor', 'Ubication',
                               help='At which floor the room is located.')

    max_adult = fields.Integer('Max Adult')
    max_child = fields.Integer('Max Child')
    capacity = fields.Integer('Capacity')
    to_be_cleaned = fields.Boolean('To be Cleaned', default=False)
    extra_beds_allowed = fields.Integer('Extra beds allowed',
                                        default='0',
                                        required=True)
    description_sale = fields.Text(
        'Sale Description', translate=True,
        help="A description of the Product that you want to communicate to "
             " your customers. This description will be copied to every Sales "
             " Order, Delivery Order and Customer Invoice/Credit Note")
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=0)

    # Business methods
    @api.multi
    def get_capacity(self, extra_bed=0):
        if not self.shared_room_id:
            return self.capacity + extra_bed
        return self.capacity
