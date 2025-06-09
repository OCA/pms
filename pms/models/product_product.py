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

    @api.depends_context("consumption_date", "board_service_line_id")
    # pylint: disable=W8110
    def _compute_product_price(self):
        super()._compute_product_price()

    @api.depends_context("consumption_date", "board_service_line_id")
    def _compute_board_price(self):
        for record in self:
            if self._context.get("board_service_line_id"):
                record.board_price = (
                    self.env["pms.board.service.room.type.line"]
                    .browse(self._context.get("board_service_line_id"))
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

    def price_compute(
        self, price_type, uom=False, currency=False, company=None, date=False
    ):
        if self._context.get("board_service_line_id"):
            price_type = "board_price"
        return super().price_compute(price_type, uom, currency, company, date)
