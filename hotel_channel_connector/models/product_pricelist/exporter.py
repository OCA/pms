# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import Component
from odoo import api, _
_logger = logging.getLogger(__name__)

class ProductPricelistExporter(Component):
    _name = 'channel.product.pricelist.exporter'
    _inherit = 'hotel.channel.exporter'
    _apply_on = ['channel.product.pricelist']
    _usage = 'product.pricelist.exporter'

    @api.model
    def rename_plan(self, binding):
        return self.backend_adapter.rename_plan(
            binding.external_id,
            binding.name)

    @api.model
    def delete_plan(self, binding):
        return self.backend_adapter.delete_plan(binding.external_id)

    @api.model
    def create_plan(self, binding):
        external_id = self.backend_adapter.create_plan(binding.name)
        binding.external_id = external_id
