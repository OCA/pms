# Copyright NuoBiT Solutions, S.L. (<https://www.nuobit.com>)
# Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component


class ChannelWubookProductPricelistListener(Component):
    _name = "channel.wubook.product.pricelist.listener"
    _inherit = "channel.wubook.listener"

    _apply_on = "product.pricelist"
