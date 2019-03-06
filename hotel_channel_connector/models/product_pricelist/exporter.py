# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo import api


class ProductPricelistExporter(Component):
    _name = 'channel.product.pricelist.exporter'
    _inherit = 'hotel.channel.exporter'
    _apply_on = ['channel.product.pricelist']
    _usage = 'product.pricelist.exporter'

    @api.model
    def rename_plan(self, binding):
        raise NotImplementedError

    @api.model
    def create_plan(self, binding):
        raise NotImplementedError

    @api.model
    def create_vplan(self, binding):
        raise NotImplementedError

    @api.model
    def modify_vplan(self, binding):
        raise NotImplementedError