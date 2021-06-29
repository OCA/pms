# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class ChannelWubookProductPricelistBinder(Component):
    _name = "channel.wubook.product.pricelist.binder"
    _inherit = "channel.wubook.binder"

    _apply_on = "channel.wubook.product.pricelist"

    # _internal_alt_id = "name"
    # _external_alt_id = "name"

    # def _get_internal_record_alt(self, model_name, values):
    #     pass

    # TODO: find pricelist by name to link to backend when there's
    # no binding
