# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo import api, fields, _
from odoo.exceptions import ValidationError


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
            raise ValidationError(_(err.data['message']))

    @api.model
    def create_plan(self, binding):
        try:
            external_id = self.backend_adapter.create_plan(binding.name)
        except ChannelConnectorError as err:
            self.create_issue(
                section='pricelist',
                internal_message=str(err),
                channel_message=err.data['message'])
            raise ValidationError(_(err.data['message']))
        else:
            binding.external_id = external_id
            self.binder.bind(external_id, binding)

    @api.model
    def create_vplan(self, binding):
        try:
            item_ids = binding.odoo_id.item_ids
            base_pricelist = item_ids.base_pricelist_id
            value = item_ids.price_discount or item_ids.price_surcharge
            dtype = 0
            # NOTE: price_discount is greater than zero for a discount
            # and lesser than zero for increasing the price a percentage
            if item_ids.price_discount > 0:
                dtype = -1
            elif item_ids.price_discount < 0:
                dtype = 1
            # NOTE: price_surcharge is greater than zero for increasing the price
            # and lesser than zero for a fixed discount
            if item_ids.price_surcharge > 0:
                dtype = 2
            elif item_ids.price_discount < 0:
                dtype = -2
            external_id = self.backend_adapter.create_vplan(
                binding.name,
                base_pricelist.channel_bind_ids.external_id,
                dtype,
                value,
            )
        except ChannelConnectorError as err:
            self.create_issue(
                section='pricelist',
                internal_message=str(err),
                channel_message=err.data['message'])
            raise ValidationError(_(err.data['message']))
        else:
            binding.external_id = external_id
            self.binder.bind(external_id, binding)

    @api.model
    def modify_vplan(self, binding):
        try:
            item_ids = binding.odoo_id.item_ids
            base_pricelist = item_ids.base_pricelist_id
            value = item_ids.price_discount or item_ids.price_surcharge
            dtype = 0
            # NOTE: price_discount is greater than zero for a discount
            # and lesser than zero for increasing the price a percentage
            if item_ids.price_discount > 0:
                dtype = -1
            elif item_ids.price_discount < 0:
                dtype = 1
            # NOTE: price_surcharge is greater than zero for increasing the price
            # and lesser than zero for a fixed discount
            if item_ids.price_surcharge > 0:
                dtype = 2
            elif item_ids.price_discount < 0:
                dtype = -2
            binding.with_context({
                'connector_no_export': True,
            }).write({'sync_date': fields.Datetime.now()})
            return self.backend_adapter.modify_vplan(
                binding.external_id,
                dtype,
                value)
        except ChannelConnectorError as err:
            self.create_issue(
                section='pricelist',
                internal_message=str(err),
                channel_message=err.data['message'])
            raise ValidationError(_(err.data['message']))
