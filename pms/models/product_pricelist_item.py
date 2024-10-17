# Copyright 2017  Alexandre Díaz, Pablo Quesada, Darío Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"
    _check_pms_properties_auto = True

    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        comodel_name="pms.property",
        relation="product_pricelist_item_pms_property_rel",
        column1="product_pricelist_item_id",
        column2="pms_property_id",
        ondelete="restrict",
        check_pms_properties=True,
    )
    date_start_consumption = fields.Date(
        string="Start Date Consumption",
        help="Start date to apply daily pricelist items",
    )
    date_end_consumption = fields.Date(
        string="End Date Consumption",
        help="End date to apply daily pricelist items",
    )
    board_service_room_type_id = fields.Many2one(
        string="Board Service",
        help="Specify a Board services on Room Types.",
        comodel_name="pms.board.service.room.type",
        index=True,
        check_pms_properties=True,
    )
    pricelist_id = fields.Many2one(
        string="Pricelist",
        help="Pricelist in which this item is included",
        index=True,
        check_pms_properties=True,
    )
    product_id = fields.Many2one(
        string="Product",
        help="Product associated with the item",
        index=True,
        check_pms_properties=True,
    )
    product_tmpl_id = fields.Many2one(
        string="Product Template",
        help="Product template associated with the item",
        index=True,
        check_pms_properties=True,
    )
    allowed_board_service_product_ids = fields.Many2many(
        string="Allowed board service products",
        comodel_name="product.product",
        store=True,
        readonly=False,
        compute="_compute_allowed_board_service_product_ids",
    )

    allowed_board_service_room_type_ids = fields.Many2many(
        string="Allowed board service room types",
        comodel_name="pms.board.service.room.type",
        store=True,
        readonly=False,
        compute="_compute_allowed_board_service_room_type_ids",
    )

    @api.depends("board_service_room_type_id")
    def _compute_allowed_board_service_product_ids(self):
        for record in self:
            domain = []
            if record.board_service_room_type_id:
                domain.append(
                    (
                        "id",
                        "in",
                        record.board_service_room_type_id.board_service_line_ids.mapped(
                            "product_id"
                        ).ids,
                    )
                )
            allowed_board_service_product_ids = self.env["product.product"].search(
                domain
            )
            record.allowed_board_service_product_ids = allowed_board_service_product_ids

    @api.depends("product_id")
    def _compute_allowed_board_service_room_type_ids(self):
        for record in self:
            allowed_board_service_room_type_ids = []
            all_board_service_room_type_ids = self.env[
                "pms.board.service.room.type"
            ].search([])
            if record.product_id:
                for board_service_room_type_id in all_board_service_room_type_ids:
                    if (
                        record.product_id
                        in board_service_room_type_id.board_service_line_ids.mapped(
                            "product_id"
                        )
                    ):
                        allowed_board_service_room_type_ids.append(
                            board_service_room_type_id.id
                        )
            else:
                allowed_board_service_room_type_ids = (
                    all_board_service_room_type_ids.ids
                )
            domain = []
            if allowed_board_service_room_type_ids:
                domain.append(("id", "in", allowed_board_service_room_type_ids))
            record.allowed_board_service_room_type_ids = (
                self.env["pms.board.service.room.type"].search(domain)
                if domain
                else False
            )

    def write(self, vals):
        # Check that the price in product room types are not
        # minor that min price in room type defined
        # REVIEW: By the momment only check fixed prices
        if "fixed_price" in vals:
            if any(
                [
                    item.product_id.room_type_id
                    and item.product_id.room_type_id.min_price
                    and vals["fixed_price"] < item.product_id.room_type_id.min_price
                    for item in self
                ]
            ):
                raise ValueError(
                    """The price in product room types can't be minor
                    that min price in room type defined"""
                )
        return super().write(vals)

    def create(self, vals):
        # Check that the price in product room types are not
        # minor that min price in room type defined
        # REVIEW: By the momment only check fixed prices
        if "fixed_price" in vals:
            product_id = self.env["product.product"].browse(vals["product_id"])
            if product_id.room_type_id and product_id.room_type_id.min_price:
                if vals["fixed_price"] < product_id.room_type_id.min_price:
                    raise ValueError(
                        """The price in product room types can't be minor
                        that min price in room type defined"""
                    )
        return super().create(vals)
