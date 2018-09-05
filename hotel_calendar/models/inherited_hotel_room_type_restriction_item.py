# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from odoo import models, fields, api
_logger = logging.getLogger(__name__)


class HotelRoomTypeResrtrictionItem(models.Model):
    _inherit = 'hotel.room.type.restriction.item'

    @api.model
    def create(self, vals):
        res = super(HotelVirtualRoomResrtrictionItem, self).create(vals)
        restrictions_parity_id = self.env['ir.default'].sudo().get(
            'res.config.settings', 'parity_restrictions_id')
        if restrictions_parity_id:
            restrictions_parity_id = int(restrictions_parity_id)
        restriction_id = res.restriction_id.id
        if restriction_id == restrictions_parity_id and \
                self.applied_on == '0_room_type':
            self.env['bus.hotel.calendar'].send_restriction_notification({
                'restriction_id': self.restriction_id.id,
                'date': self.date_start,
                'min_stay': self.min_stay,
                'min_stay_arrival': self.min_stay_arrival,
                'max_stay': self.max_stay,
                'max_stay_arrival': self.max_stay_arrival,
                'closed': self.closed,
                'closed_departure': self.closed_departure,
                'closed_arrival': self.closed_arrival,
                'room_type_id': self.room_type_id.id,
                'id': self.id,
            })
        return res

    @api.multi
    def write(self, vals):
        restrictions_parity_id = self.env['ir.default'].sudo().get(
            'res.config.settings', 'parity_restrictions_id')
        if restrictions_parity_id:
            restrictions_parity_id = int(restrictions_parity_id)
        ret_vals = super(HotelVirtualRoomResrtrictionItem, self).write(vals)

        bus_hotel_calendar_obj = self.env['bus.hotel.calendar']
        for record in self:
            if record.restriction_id.id != restrictions_parity_id or \
                    record.applied_on != '0_room_type':
                continue
            bus_hotel_calendar_obj.send_restriction_notification({
                'restriction_id': record.restriction_id.id,
                'date': record.date_start,
                'min_stay': record.min_stay,
                'min_stay_arrival': record.min_stay_arrival,
                'max_stay': record.max_stay,
                'max_stay_arrival': record.max_stay_arrival,
                'closed': record.closed,
                'closed_departure': record.closed_departure,
                'closed_arrival': record.closed_arrival,
                'room_type_id': record.room_type_id.id,
                'id': record.id,
            })
        return ret_vals

    @api.multi
    def unlink(self):
        restrictions_parity_id = self.env['ir.default'].sudo().get(
            'res.config.settings', 'parity_restrictions_id')
        if restrictions_parity_id:
            restrictions_parity_id = int(restrictions_parity_id)
        # Construct dictionary with relevant info of removed records
        unlink_vals = []
        for record in self:
            if record.restriction_id.id != restrictions_parity_id or \
                    record.applied_on != '0_room_type':
                continue
            unlink_vals.append({
                'restriction_id': record.restriction_id.id,
                'date': record.date_start,
                'min_stay': 0,
                'min_stay_arrival': 0,
                'max_stay': 0,
                'max_stay_arrival': 0,
                'closed': False,
                'closed_departure': False,
                'closed_arrival': False,
                'room_type_id': record.room_type_id.id,
                'id': record.id,
            })
        res = super(HotelVirtualRoomResrtrictionItem, self).unlink()
        bus_hotel_calendar_obj = self.env['bus.hotel.calendar']
        for uval in unlink_vals:
            bus_hotel_calendar_obj.send_restriction_notification(uval)
        return res
