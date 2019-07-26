# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo import api, fields, _
from odoo.exceptions import ValidationError


class HotelRoomTypeRestrictionExporter(Component):
    _inherit = 'channel.hotel.room.type.restriction.exporter'

    @api.model
    def rename_rplan(self, binding):
        try:
            binding.with_context({
                'connector_no_export': True,
            }).write({'sync_date': fields.Datetime.now()})
            return self.backend_adapter.rename_rplan(
                binding.external_id,
                binding.name)
        except ChannelConnectorError as err:
            self.create_issue(
                section='restriction',
                internal_message=str(err),
                channel_message=err.data['message'])
            raise ValidationError(_(err.data['message']))

    @api.model
    def create_rplan(self, binding):
        try:
            external_id = self.backend_adapter.create_rplan(binding.name)
        except ChannelConnectorError as err:
            self.create_issue(
                section='restriction',
                internal_message=str(err),
                channel_message=err.data['message'])
            raise ValidationError(_(err.data['message']))
        else:
            self.binder.bind(external_id, binding)
