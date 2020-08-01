# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsBoardServiceRoomTypeLine(models.Model):
    _name = "pms.board.service.room.type.line"
    _description = "Services on Board Service included in Room"

    # Fields declaration
    pms_board_service_room_type_id = fields.Many2one(
        "pms.board.service.room.type",
        "Board Service Room",
        ondelete="cascade",
        required=True,
    )
    product_id = fields.Many2one(
        "product.product", "Product", required=True, readonly=True
    )
    # TODO def default_amount "amount of service"
    amount = fields.Float("Amount", digits=("Product Price"), default=0.0)
