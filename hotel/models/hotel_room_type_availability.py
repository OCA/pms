# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HotelRoomTypeAvailability(models.Model):
    _name = 'hotel.room.type.availability'
    _inherit = 'mail.thread'

    room_type_id = fields.Many2one('hotel.room.type', 'Room Type',
                                   required=True, track_visibility='always',
                                   ondelete='cascade')
    avail = fields.Integer('Avail', default=0, track_visibility='always')
    date = fields.Date('Date', required=True, track_visibility='always')

    _sql_constraints = [
        ('room_type_registry_unique',
         'unique(room_type_id, date)',
         'Only can exists one availability in the same day for the same room type!')
    ]

    @api.constrains('avail')
    def _check_avail(self):
        for record in self:
            if record.avail < 0:
                record.avail = 0
            else:
                room_type_obj = self.env['hotel.room.type']
                cavail = len(room_type_obj.check_availability_room(
                    record.date,
                    record.date,
                    room_type_id=record.room_type_id.id))
                max_avail = min(cavail, record.room_type_id.total_rooms_count)
                if record.avail > max_avail:
                    record.avail = max_avail
