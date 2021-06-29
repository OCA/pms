# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import ValidationError

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class ChannelWubookProductPricelistItemMapperExport(Component):
    _name = "channel.wubook.product.pricelist.item.mapper.export"
    _inherit = "channel.wubook.mapper.export"

    _apply_on = "channel.wubook.product.pricelist.item"

    @mapping
    def item(self, record):
        values = {}
        if record.wubook_item_type == "virtual":
            if record.price_surcharge and record.price_discount:
                raise ValidationError(
                    _(
                        "Unsupported combination of 'Discount' and 'Price'. Either "
                        "'Discount' or 'Price' must be defined but not both."
                    )
                )
            if record.price_discount:
                values.update(
                    {
                        "variation_type": record.price_discount < 0 and 1 or -1,
                        "variation": abs(record.price_discount),
                    }
                )
            if record.price_surcharge:
                values.update(
                    {
                        "variation_type": record.price_surcharge < 0 and -2 or 2,
                        "variation": abs(record.price_surcharge),
                    }
                )
            pricelist = record.base_pricelist_id
            binder = self.binder_for("channel.wubook.product.pricelist")
            external_id = binder.to_external(pricelist, wrap=True)
            if not external_id:
                raise ValidationError(
                    _(
                        "External record of Pricelist id '%s' does not exists. "
                        "It should be exported in _export_dependencies"
                    )
                    % pricelist.name
                )
            values["rid"] = external_id
        elif record.wubook_item_type == "standard":
            if record.date_start_consumption != record.date_end_consumption:
                raise ValidationError(_("The dates must be the same"))
            values["date"] = record.date_start_consumption
            values["price"] = record.fixed_price

            room_type = self.env["pms.room.type"].search(
                [
                    ("product_id", "=", record.product_id.id),
                ]
            )
            if len(room_type) != 1:
                raise ValidationError(
                    _("Unexpected number of Room Types found %s") % len(room_type)
                )
            binder = self.binder_for("channel.wubook.pms.room.type")
            external_id = binder.to_external(room_type, wrap=True)
            if not external_id:
                raise ValidationError(
                    _(
                        "External record of Room Type id [%s] %s does not exists. "
                        "It should be exported in _export_dependencies"
                    )
                    % (room_type.default_code, room_type.name)
                )
            values["rid"] = external_id

        return values
