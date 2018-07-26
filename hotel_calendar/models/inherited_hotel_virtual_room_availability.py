# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class HotelVirtualRoomAvailability(models.Model):
    _inherit = 'hotel.virtual.room.availability'

    @api.model
    def create(self, vals):
        res = super(HotelVirtualRoomAvailability, self).create(vals)
        self.env['bus.hotel.calendar'].send_availability_notification({
            'date': res.date,
            'avail': res.avail,
            'no_ota': res.no_ota,
            'virtual_room_id': res.virtual_room_id.id,
            'id': res.id,
        })
        return res

    @api.multi
    def write(self, vals):
        ret_vals = super(HotelVirtualRoomAvailability, self).write(vals)
        bus_hotel_calendar_obj = self.env['bus.hotel.calendar']
        for record in self:
            bus_hotel_calendar_obj.send_availability_notification({
                'date': record.date,
                'avail': record.avail,
                'no_ota': record.no_ota,
                'virtual_room_id': record.virtual_room_id.id,
                'id': record.id,
            })
        return ret_vals

    @api.multi
    def unlink(self):
        # Construct dictionary with relevant info of removed records
        unlink_vals = []
        for record in self:
            unlink_vals.append({
                'date': record.date,
                'avail': record.virtual_room_id.max_real_rooms,
                'virtual_room_id': record.virtual_room_id.id,
                'no_ota': False,
                'id': record.id,
            })
        res = super(HotelVirtualRoomAvailability, self).unlink()
        bus_hotel_calendar_obj = self.env['bus.hotel.calendar']
        for uval in unlink_vals:
            bus_hotel_calendar_obj.send_availability_notification(uval)
        return res
