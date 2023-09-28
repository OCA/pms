# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ChannelWubookProductPricelistItemBinder(Component):
    _name = "channel.wubook.product.pricelist.item.binder"
    _inherit = "channel.wubook.binder"

    _apply_on = "channel.wubook.product.pricelist.item"
