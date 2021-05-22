from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    board_price = fields.Float(
        string="Board Service Price",
        help="Get price on board service",
        digits="Product Price",
        compute="_compute_board_price",
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

    def price_compute(self, price_type, uom=False, currency=False, company=None):
        if self._context.get("board_service"):
            price_type = "board_price"
        return super(ProductProduct, self).price_compute(
            price_type, uom, currency, company
        )
