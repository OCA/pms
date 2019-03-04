# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector_wubook.components.backend_adapter import (
    WUBOOK_STATUS_CONFIRMED,
    WUBOOK_STATUS_WAITING,
    WUBOOK_STATUS_REFUSED,
    WUBOOK_STATUS_ACCEPTED,
    WUBOOK_STATUS_CANCELLED,
    WUBOOK_STATUS_CANCELLED_PENALTY,
    WUBOOK_STATUS_BAD,
    WUBOOK_STATUS_GOOD)


class ChannelHotelReservation(models.Model):
    _inherit = 'channel.hotel.reservation'

    channel_status = fields.Selection(selection_add=[
        (str(WUBOOK_STATUS_CONFIRMED), 'Confirmed'),
        (str(WUBOOK_STATUS_WAITING), 'Waiting'),
        (str(WUBOOK_STATUS_REFUSED), 'Refused'),
        (str(WUBOOK_STATUS_ACCEPTED), 'Accepted'),
        (str(WUBOOK_STATUS_CANCELLED), 'Cancelled'),
        (str(WUBOOK_STATUS_CANCELLED_PENALTY), 'Cancelled with penalty'),
    ])


class HotelReservation(models.Model):
    _inherit = 'hotel.reservation'

    @api.multi
    def action_cancel(self):
        for record in self:
            # Can't cancel in Odoo
            if record.is_from_ota and self._context.get('ota_limits', True):
                raise ValidationError(_("Can't cancel reservations from OTA's"))
        user = self.env['res.users'].browse(self.env.uid)
        if user.has_group('hotel.group_hotel_call'):
            self.write({'to_read': True, 'to_assign': True})

        res = super(HotelReservation, self).action_cancel()
        for record in self:
            # Only can cancel reservations created directly in wubook
            for binding in record.channel_bind_ids:
                if binding.external_id and not binding.ota_id and \
                        int(binding.channel_status) in WUBOOK_STATUS_GOOD:
                    self.env['channel.hotel.reservation']._event('on_record_cancel').notify(binding)
        return res

    @api.multi
    def confirm(self):
        for record in self:
            if record.is_from_ota:
                for binding in record.channel_bind_ids:
                    if int(binding.channel_status) in WUBOOK_STATUS_BAD \
                            and self._context.get('ota_limits', True):
                        raise ValidationError(_("Can't confirm OTA's cancelled reservations"))
        return super(HotelReservation, self).confirm()


class HotelReservationAdapter(Component):
    _name = 'channel.hotel.reservation.adapter'
    _inherit = 'wubook.adapter'
    _apply_on = 'channel.hotel.reservation'

    def mark_bookings(self, channel_reservation_ids):
        return super(HotelReservationAdapter, self).mark_bookings(
            channel_reservation_ids)

    def fetch_new_bookings(self):
        return super(HotelReservationAdapter, self).fetch_new_bookings()

    def fetch_booking(self, channel_reservation_id):
        return super(HotelReservationAdapter, self).fetch_booking(
            channel_reservation_id)

    def cancel_reservation(self, channel_reservation_id, message):
        return super(HotelReservationAdapter, self).cancel_reservation(
            channel_reservation_id, message)
