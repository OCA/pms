# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo import api, _, fields


class ProductPricelistExporter(Component):
    _inherit = 'channel.product.pricelist.exporter'

    @api.model
    def update_plan_name(self, binding):
        try:
            binding.with_context({
                'connector_no_export': True,
            }).write({'sync_date': fields.Datetime.now()})
            return self.backend_adapter.update_plan_name(
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

    @api.model
    def create_vplan(self, binding):
        try:
            import wdb; wdb.set_trace()
            external_id = self.backend_adapter.create_vplan(
                binding.name,
                binding.pid,
                binding.dtype,
                binding.value,
            )
        except ChannelConnectorError as err:
            self.create_issue(
                section='pricelist',
                internal_message=str(err),
                channel_message=err.data['message'])
        else:
            binding.external_id = external_id
            self.binder.bind(external_id, binding)