# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, _, fields
from odoo.exceptions import ValidationError


class HotelCalendar(models.Model):
    """ Used to show and filter rooms and reservations in the PMS Calendar. """
    _name = 'hotel.calendar'

    # Default methods
    @api.model
    def _get_default_hotel(self):
        return self.env.user.hotel_id

    # Fields declaration
    name = fields.Char('Name', required=True)
    hotel_id = fields.Many2one('hotel.property', 'Hotel', required=True, ondelete='restrict',
                               default=_get_default_hotel)
    room_type_ids = fields.Many2many('hotel.room.type', string='Room Type')
    segmentation_ids = fields.Many2many('hotel.room.type.class', string='Segmentation')
    location_ids = fields.Many2many('hotel.floor', string='Location')
    amenity_ids = fields.Many2many('hotel.amenity', string='Amenity')

