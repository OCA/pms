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

    def price_compute(self, price_type, uom=False, currency=False, company=None):
        if self._context.get("board_service"):
            price_type = "board_price"
        return super(ProductProduct, self).price_compute(
            price_type, uom, currency, company
        )
