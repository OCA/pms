# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo import api, _

class HotelReservationExporter(Component):
    _inherit = 'channel.hotel.reservation.exporter'

    @api.model
    def cancel_reservation(self, binding):
        user = self.env['res.user'].browse(self.env.uid)
        try:
            return self.backend_adapter.cancel_reservation(
                binding.external_id,
                _('Cancelled by %s') % user.partner_id.name)
        except ChannelConnectorError as err:
            self.create_issue(
                section='reservation',
                internal_message=str(err),
                channel_object_id=binding.external_id,
                channel_message=err.data['message'])

    @api.model
    def mark_booking(self, binding):
        try:
            return self.backend_adapter.mark_bookings([binding.external_id])
        except ChannelConnectorError as err:
            self.create_issue(
                section='reservation',
                internal_message=str(err),
                channel_object_id=binding.external_id,
                channel_message=err.data['message'])

    @api.model
    def mark_bookings(self, external_ids):
        try:
            return self.backend_adapter.mark_bookings(external_ids)
        except ChannelConnectorError as err:
            self.create_issue(
                section='reservation',
                internal_message=str(err),
                channel_object_id=external_ids,
                channel_message=err.data['message'])
