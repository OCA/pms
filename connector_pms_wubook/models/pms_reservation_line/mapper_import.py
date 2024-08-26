# Copyright 2021 Eric Antones <eantones@nuobit.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector_pms_wubook.models.pms_reservation.mapper_import import (
    get_board_service_room_type,
    get_room_type,
)


class ChannelWubookPmsReservationLineMapperImport(Component):
    _name = "channel.wubook.pms.reservation.line.mapper.import"
    _inherit = "channel.wubook.mapper.import"

    _apply_on = "channel.wubook.pms.reservation.line"

    direct = [
        ("day", "date"),
    ]

    @mapping
    def price(self, record):
        price = record["price"]
        room_type = get_room_type(self, record["room_id"])
        # REVIEW: Wubook send vat_included False in cases that the price is
        # already included. Deactivate this line while is not clear
        vat_included = record["vat_included"]
        # By default, taxes are included in the price
        # if not included, we need handle the price
        if not vat_included:
            product = room_type.product_id
            company = self.backend_record.pms_property_id.company_id
            taxes = product.taxes_id.filtered(lambda x: x.company_id == company)
            taxes_vals = taxes.compute_all(
                price_unit=price, product=product, handle_price_include=vat_included
            )
            price = taxes_vals["total_included"]
        if record["board"] and record["board_included"]:
            board_service_room = get_board_service_room_type(
                self, room_type, record["board"]
            )
            # occupancy is the adults in the reservation
            board_day_price_adults = (
                sum(
                    board_service_room.board_service_line_ids.with_context(
                        property=self.backend_record.pms_property_id.id
                    )
                    .filtered(lambda line: line.adults)
                    .mapped("amount")
                )
                * record["occupancy"]
            )
            board_day_price_children = (
                sum(
                    board_service_room.board_service_line_ids.with_context(
                        property=self.backend_record.pms_property_id.id
                    )
                    .filtered(lambda line: line.children)
                    .mapped("amount")
                )
                * record["children"]
            )
            price -= board_day_price_adults + board_day_price_children
        return {"price": price}
