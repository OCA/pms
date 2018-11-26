# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo import api


class ProductPricelistDeleter(Component):
    _name = 'channel.product.pricelist.deleter'
    _inherit = 'hotel.channel.deleter'
    _apply_on = ['channel.product.pricelist']
    _usage = 'product.pricelist.deleter'

    @api.model
    def delete_plan(self, binding):
        raise NotImplementedError
