# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ProducrPricelistItemAdapter(Component):
    _name = 'channel.product.pricelist.item.adapter'
    _inherit = 'wubook.adapter'
    _apply_on = 'channel.product.pricelist.item'

    def fetch_plan_prices(self, external_id, date_from, date_to, rooms):
        return super(ProducrPricelistItemAdapter, self).fetch_plan_prices(
            external_id,
            date_from,
            date_to,
            rooms)
