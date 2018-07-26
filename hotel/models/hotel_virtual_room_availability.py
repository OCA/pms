# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <alex@aloxa.eu>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)


class HotelVirtualRoomAvailability(models.Model):
    _inherit = 'mail.thread'
    _name = 'hotel.virtual.room.availability'

    # virtual_room_id = fields.Many2one('hotel.virtual.room', 'Virtual Room',
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

    _sql_constraints = [('vroom_registry_unique', 'unique(room_type_id, date)',
                         'Only can exists one availability in the same day for the same room type!')]

    @api.constrains('avail')
    def _check_avail(self):
        if self.avail < 0:
            self.avail = 0

        vroom_obj = self.env['hotel.room.type']
        cavail = len(vroom_obj.check_availability_virtual_room(
            self.date,
            self.date,
            room_type_id=self.room_type_id.id))
        max_avail = min(cavail,
                        self.room_type_id.total_rooms_count)
        if self.avail > max_avail:
            self.avail = max_avail

    @api.constrains('date', 'room_type_id')
    def _check_date_virtual_room_id(self):
        count = self.search_count([
            ('date', '=', self.date),
            ('room_type_id', '=', self.room_type_id.id)
        ])
        if count > 1:
            raise ValidationError(_("can't assign the same date to more than \
                                    one room type"))
