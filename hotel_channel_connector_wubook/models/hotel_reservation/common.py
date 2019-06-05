# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
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
    modified_reservations = fields.Char('Code Modifications')

    # TODO: Review where to check the total room amount
    # @api.model
    # def create(self, vals):
    #     record = super(ChannelHotelReservation, self).create(vals)
    #     if record.channel_total_amount != record.odoo_id.price_room_services_set:
    #         record.odoo_id.unconfirmed_channel_price = True
    #         self.env['hotel.channel.connector.issue'].create({
    #             'backend_id': record.backend_id.id,
    #             'section': 'reservation',
    #             'internal_message': "Disagreement in reservation price. Odoo marked %.2f whereas the channel sent %.2f." % (
    #                 record.odoo_id.price_room_services_set,
    #                 record.channel_total_amount),
    #             'channel_message': 'Please, review the board services included in the reservation.',
    #             'channel_object_id': record.external_id
    #         })
    #
    #     return record


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
            self.write({'to_assign': True})

        return super(HotelReservation, self).action_cancel()

    @api.multi
    def confirm(self):
        for record in self:
            if record.is_from_ota:
                for binding in record.channel_bind_ids:
                    if int(binding.channel_status) in WUBOOK_STATUS_BAD \
                            and self._context.get('ota_limits', True):
                        raise ValidationError(_("Can't confirm OTA's cancelled reservations"))
        return super(HotelReservation, self).confirm()


class BindingHotelReservationListener(Component):
    _name = 'binding.hotel.reservation.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['hotel.reservation']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):

        fields_to_check = ('state', )
        fields_checked = [elm for elm in fields_to_check if elm in fields]
        if any(fields_checked):
            if any(record.channel_bind_ids):
                # Only can cancel reservations created directly in wubook
                for binding in record.channel_bind_ids:
                    if binding.external_id and not binding.ota_id and \
                            int(binding.channel_status) in WUBOOK_STATUS_GOOD:
                        if record.state in ('cancelled'):
                            binding.sudo().cancel_reservation()
                        # self.env['channel.hotel.reservation']._event('on_record_cancel').notify(binding)


class HotelReservationAdapter(Component):
    _name = 'channel.hotel.reservation.adapter'
    _inherit = 'wubook.adapter'
    _apply_on = 'channel.hotel.reservation'

    def mark_bookings(self, channel_reservation_ids):
        return super(HotelReservationAdapter, self).mark_bookings(
            channel_reservation_ids)

    def fetch_new_bookings(self):
        return super(HotelReservationAdapter, self).fetch_new_bookings()

    def fetch_bookings(self, dfrom, dto):
        return super(HotelReservationAdapter, self).fetch_bookings(dfrom, dto)

    def fetch_booking(self, channel_reservation_id):
        return super(HotelReservationAdapter, self).fetch_booking(
            channel_reservation_id)

    def cancel_reservation(self, channel_reservation_id, message):
        return super(HotelReservationAdapter, self).cancel_reservation(
            channel_reservation_id, message)
