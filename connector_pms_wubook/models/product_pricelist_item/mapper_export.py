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
            if record.price_surcharge:
                values.update(
                    {
                        "variation_type": record.price_surcharge < 0 and -2 or 2,
                        "variation": abs(record.price_surcharge),
                    }
                )
            if not values:
                values.update(
                    {
                        "variation_type": record.price_discount < 0 and 1 or -1,
                        "variation": abs(record.price_discount),
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
            # If board service default is defined, we need sum the price of the board service
            # to the price of the room type (wubook does not separate the price of the room
            # type from the price of the board service in this case)
            board_service_default = self.env["pms.board.service.room.type"].search(
                [
                    ("pms_room_type_id", "=", room_type.id),
                    ("by_default", "=", True),
                    ("pms_property_id", "=", record.backend_id.pms_property_id.id),
                ]
            )
            if board_service_default:
                # TODO: get board service price with date context
                # (view _get_price_unit_line method in pms_service.py)
                values[
                    "price"
                ] += board_service_default.amount * room_type.get_room_type_capacity(
                    pms_property_id=record.backend_id.pms_property_id.id
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
