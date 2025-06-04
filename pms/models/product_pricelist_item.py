# Copyright 2017  Alexandre Díaz, Pablo Quesada, Darío Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models, tools


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"
    _order = (
        "applied_on, min_quantity desc, categ_id desc, has_properties desc, id desc"
    )
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
        string="Product", help="Product associated with the item", index=True
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
    has_properties = fields.Boolean(compute="_compute_has_properties", store=True)

    @api.depends("pms_property_ids")
    def _compute_has_properties(self):
        """Compute if the pricelist has properties associated."""
        for record in self:
            record.has_properties = len(record.pms_property_ids) != 0

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

    def _compute_consumption_price(
        self, product, quantity, uom, date, currency=None, **kwargs
    ):
        """Override to add the consuption date parameter to the price computation

        :param product: recordset of product (product.product/product.template)
        :param float qty: quantity of products requested (in given uom)
        :param uom: unit of measure (uom.uom record)
        :param datetime date: date to use for price computation and currency conversions
        :param currency: pricelist currency (for the specific case where self is empty)
        :param **kwargs: optional context arguments, useful for
            consumption date price computation

        :returns: price according to pricelist rule, expressed in pricelist currency
        :rtype: float
        """
        product.ensure_one()
        uom.ensure_one()

        currency = currency or self.currency_id
        currency.ensure_one()

        # Pricelist specific values are specified according to product UoM
        # and must be multiplied according to the factor between uoms
        product_uom = product.uom_id
        if product_uom != uom:

            def convert(p):
                return product_uom._compute_consumption_price(p, uom)

        else:

            def convert(p):
                return p

        if self.compute_price == "fixed":
            price = convert(self.fixed_price)
        elif self.compute_price == "percentage":
            base_price = self._compute_base_consumption_price(
                product, quantity, uom, date, currency, **kwargs
            )
            price = (base_price - (base_price * (self.percent_price / 100))) or 0.0
        elif self.compute_price == "formula":
            base_price = self._compute_base_consumption_price(
                product, quantity, uom, date, currency, **kwargs
            )
            # complete formula
            price_limit = base_price
            price = (base_price - (base_price * (self.price_discount / 100))) or 0.0
            if self.price_round:
                price = tools.float_round(price, precision_rounding=self.price_round)

            if self.price_surcharge:
                price += convert(self.price_surcharge)

            if self.price_min_margin:
                price = max(price, price_limit + convert(self.price_min_margin))

            if self.price_max_margin:
                price = min(price, price_limit + convert(self.price_max_margin))
        else:  # empty self, or extended pricelist price computation logic
            price = self._compute_base_consumption_price(
                product, quantity, uom, date, currency, **kwargs
            )

        return price

    def _compute_base_consumption_price(
        self, product, quantity, uom, date, target_currency, **kwargs
    ):
        """Compute the base price for a given rule

        :param product: recordset of product (product.product/product.template)
        :param float qty: quantity of products requested (in given uom)
        :param uom: unit of measure (uom.uom record)
        :param datetime date: date to use for price computation and currency conversions
        :param target_currency: pricelist currency

        :returns: base price, expressed in provided pricelist currency
        :rtype: float
        """
        target_currency.ensure_one()

        rule_base = self.base or "list_price"
        if rule_base == "pricelist" and self.base_pricelist_id:
            price = self.base_pricelist_id._get_product_price(
                product, quantity, uom, date, **kwargs
            )
            src_currency = self.base_pricelist_id.currency_id
        elif rule_base == "standard_price":
            src_currency = product.cost_currency_id
            price = product.price_compute(rule_base, uom=uom, date=date)[product.id]
        else:  # list_price
            src_currency = product.currency_id
            price = product.price_compute(rule_base, uom=uom, date=date)[product.id]

        if src_currency != target_currency:
            price = src_currency._convert(
                price, target_currency, self.env.company, date, round=False
            )
        return price
