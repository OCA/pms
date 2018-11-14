# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo import api, _
_logger = logging.getLogger(__name__)

class ProductPricelistExporter(Component):
    _name = 'channel.product.pricelist.exporter'
    _inherit = 'hotel.channel.exporter'
    _apply_on = ['channel.product.pricelist']
    _usage = 'product.pricelist.exporter'

    @api.model
    def rename_plan(self, binding):
        try:
            return self.backend_adapter.rename_plan(
                binding.external_id,
                binding.name)
        except ChannelConnectorError as err:
            self.create_issue(
                section='pricelist',
                internal_message=str(err),
                channel_message=err.data['message'])

    @api.model
    def create_plan(self, binding):
        try:
            external_id = self.backend_adapter.create_plan(binding.name)
        except ChannelConnectorError as err:
            self.create_issue(
                section='pricelist',
                internal_message=str(err),
                channel_message=err.data['message'])
        else:
            binding.external_id = external_id
            self.binder.bind(external_id, binding)
