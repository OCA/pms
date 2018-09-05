# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)


class HotelRoomTypeAvailability(models.Model):
    _inherit = 'mail.thread'
    _name = 'hotel.room.type.availability'

    # room_type_id = fields.Many2one('hotel.virtual.room', 'Virtual Room',
    #                                   required=True, track_visibility='always',
    #                                   ondelete='cascade')
    room_type_id = fields.Many2one('hotel.room.type', 'Room Type',
                                   required=True, track_visibility='always',
                                   ondelete='cascade')
    avail = fields.Integer('Avail', default=0, track_visibility='always')
    no_ota = fields.Boolean('No OTA', default=False, track_visibility='always')
    booked = fields.Boolean('Booked', default=False, readonly=True,
                            track_visibility='always')
    date = fields.Date('Date', required=True, track_visibility='always')

    _sql_constraints = [
        ('room_type_registry_unique',
         'unique(room_type_id, date)',
         'Only can exists one availability in the same day for the same room type!')
    ]

    @api.constrains('avail')
    def _check_avail(self):
        if self.avail < 0:
            self.avail = 0

        room_type_obj = self.env['hotel.room.type']
        cavail = len(room_type_obj.check_availability_room(
            self.date,
            self.date,
            room_type_id=self.room_type_id.id))
        max_avail = min(cavail,
                        self.room_type_id.total_rooms_count)
        if self.avail > max_avail:
            self.avail = max_avail

    @api.constrains('date', 'room_type_id')
    def _check_date_room_type_id(self):
        count = self.search_count([
            ('date', '=', self.date),
            ('room_type_id', '=', self.room_type_id.id)
        ])
        if count > 1:
            raise ValidationError(_("can't assign the same date to more than \
                                    one room type"))
