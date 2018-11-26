# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo import api


class ProductPricelistItemExporter(Component):
    _name = 'channel.product.pricelist.item.exporter'
    _inherit = 'hotel.channel.exporter'
    _apply_on = ['channel.product.pricelist.item']
    _usage = 'product.pricelist.item.exporter'

    @api.model
    def push_pricelist(self):
        raise NotImplementedError
