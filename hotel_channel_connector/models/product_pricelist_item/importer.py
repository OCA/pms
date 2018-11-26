# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo import api


class ProductPricelistItemImporter(Component):
    _name = 'channel.product.pricelist.item.importer'
    _inherit = 'hotel.channel.importer'
    _apply_on = ['channel.product.pricelist.item']
    _usage = 'product.pricelist.item.importer'

    @api.model
    def import_all_pricelist_values(self, date_from, date_to, rooms=None):
        raise NotImplementedError

    @api.model
    def import_pricelist_values(self, external_id, date_from, date_to, rooms=None):
        raise NotImplementedError
