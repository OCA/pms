from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductProduct(models.Model):
    _inherit = "product.product"

    board_price = fields.Float(
        string="Board Service Price",
        help="Get price on board service",
        digits="Product Price",
        compute="_compute_board_price",
    )

    room_type_id = fields.Many2one(
        string="Room Type",
        comodel_name="pms.room.type",
        compute="_compute_room_type_id",
    )

    @api.depends_context("consumption_date")
    def _compute_product_price(self):
        super(ProductProduct, self)._compute_product_price()

    def _compute_board_price(self):
        for record in self:
            if self._context.get("board_service"):
                record.board_price = (
                    self.env["pms.board.service.room.type.line"]
                    .search(
                        [
                            (
                                "pms_board_service_room_type_id",
                                "=",
                                self._context.get("board_service"),
                            ),
                            ("product_id", "=", record.id),
                        ]
                    )
                    .amount
                )
            else:
                record.board_price = False

    def _compute_room_type_id(self):
        for rec in self:
            room_type = self.env["pms.room.type"].search(
                [
                    ("product_id", "=", rec.id),
                ]
            )
            if room_type:
                if len(room_type) > 1:
                    raise ValidationError(
                        _("More than one room found for the same product")
                    )
                rec.room_type_id = room_type
            else:
                rec.room_type_id = False

    def price_compute(self, price_type, uom=False, currency=False, company=None):
        if self._context.get("board_service"):
            price_type = "board_price"
        return super(ProductProduct, self).price_compute(
            price_type, uom, currency, company
        )

    @api.model
    def _pms_get_display_price(
        self, pricelist_id, product, company_id, product_qty=1, partner_id=False
    ):
        pricelist = self.env["product.pricelist"].browse(pricelist_id)
        partner = self.env["res.partner"].browse(partner_id) if partner_id else False
        if pricelist.discount_policy == "with_discount":
            return product.price
        final_price, rule_id = pricelist.with_context(
            product._context
        ).get_product_price_rule(product, product_qty or 1.0, partner)
        base_price, currency_id = self.with_context(
            product._context
        )._pms_get_real_price_currency(
            product,
            rule_id,
            product_qty,
            product.uom_id,
            pricelist.id,
            company_id,
            partner_id,
        )
        if currency_id != pricelist.currency_id.id:
            base_price = (
                self.env["res.currency"]
                .browse(currency_id)
                .with_context(product._context)
                .compute(base_price, pricelist.currency_id)
            )
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    @api.model
    def _pms_get_real_price_currency(
        self,
        product,
        rule_id,
        qty,
        uom,
        pricelist_id,
        company_id=False,
        partner_id=False,
    ):
        """Retrieve the price before applying the pricelist
        :param obj product: object of current product record
        :parem float qty: total quantity of product
        :param tuple price_and_rule: tuple(price, suitable_rule)
            coming from pricelist computation
        :param obj uom: unit of measure of current order line
        :param integer pricelist_id: pricelist id of sales order"""
        PricelistItem = self.env["product.pricelist.item"]
        field_name = "lst_price"
        currency_id = None
        product_currency = product.currency_id
        company = self.env["res.company"].browse(company_id) if company_id else False
        partner = self.env["res.partner"].browse(partner_id) if partner_id else False
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            if pricelist_item.pricelist_id.discount_policy == "without_discount":
                while (
                    pricelist_item.base == "pricelist"
                    and pricelist_item.base_pricelist_id
                    and pricelist_item.base_pricelist_id.discount_policy
                    == "without_discount"
                ):
                    price, rule_id = pricelist_item.base_pricelist_id.with_context(
                        uom=uom.id
                    ).get_product_price_rule(product, qty, partner)
                    pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == "standard_price":
                field_name = "standard_price"
                product_currency = product.cost_currency_id
            elif (
                pricelist_item.base == "pricelist" and pricelist_item.base_pricelist_id
            ):
                field_name = "price"
                product = product.with_context(
                    pricelist=pricelist_item.base_pricelist_id.id
                )
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(
                    product_currency,
                    currency_id,
                    company,
                    fields.Date.today(),
                )

        product_uom = self.env.context.get("uom") or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id
