# Copyright 2018-2019 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api


class HotelRoomTypeAvailability(models.Model):
    _inherit = 'hotel.room.type.availability'

    def _prepare_notif_values(self, record):
        return {
            'date': record.date,
            'quota': record.quota,
            'no_ota': record.no_ota,
            'max_avail': record.max_avail,
            'room_type_id': record.room_type_id.id,
            'id': record.id,
            'channel_avail': record.channel_bind_ids.channel_avail,
        }

    @api.model
    def create(self, vals):
        res = super(HotelRoomTypeAvailability, self).create(vals)
        self.env['bus.hotel.calendar'].send_availability_notification(
            self._prepare_notif_values(res)
        )
        return res

    @api.multi
    def write(self, vals):
        ret_vals = super(HotelRoomTypeAvailability, self).write(vals)
        bus_hotel_calendar_obj = self.env['bus.hotel.calendar']
        for record in self:
            bus_hotel_calendar_obj.send_availability_notification(
                self._prepare_notif_values(record)
            )
        return ret_vals

    @api.multi
    def unlink(self):
        # Construct dictionary with relevant info of removed records
        unlink_vals = []
        for record in self:
            unlink_vals.append(
                self._prepare_notif_values(record)
            )
        res = super(HotelRoomTypeAvailability, self).unlink()
        bus_hotel_calendar_obj = self.env['bus.hotel.calendar']
        for uval in unlink_vals:
            bus_hotel_calendar_obj.send_availability_notification(uval)
        return res
