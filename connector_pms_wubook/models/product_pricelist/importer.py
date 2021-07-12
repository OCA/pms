# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component


class ChannelWubookProductPricelistDelayedBatchImporter(Component):
    _name = "channel.wubook.product.pricelist.delayed.batch.importer"
    _inherit = "channel.wubook.delayed.batch.importer"

    _apply_on = "channel.wubook.product.pricelist"


class ChannelWubookProductPricelistDirectBatchImporter(Component):
    _name = "channel.wubook.product.pricelist.direct.batch.importer"
    _inherit = "channel.wubook.direct.batch.importer"

    _apply_on = "channel.wubook.product.pricelist"


class ChannelWubookProductPricelistImporter(Component):
    _name = "channel.wubook.product.pricelist.importer"
    _inherit = "channel.wubook.importer"

    _apply_on = "channel.wubook.product.pricelist"

    def _import_dependencies(self, external_data, external_fields):
        pricelist_type = external_data["type"]
        if pricelist_type == "standard":
            self._import_dependency(
                [x["rid"] for x in external_data.get("items", [])],
                "channel.wubook.pms.room.type",
            )
        elif pricelist_type == "virtual":
            self._import_dependency(
                [x["vpid"] for x in external_data.get("items", [])],
                "channel.wubook.product.pricelist",
            )
        else:
            raise ValidationError(_("Pricelist type %s not valid") % pricelist_type)
