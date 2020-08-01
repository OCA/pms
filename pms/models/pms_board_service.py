# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PmsBoardService(models.Model):
    _name = "pms.board.service"
    _description = "Board Services"

    # Fields declaration
    name = fields.Char("Board Name", translate=True, size=64, required=True, index=True)
    board_service_line_ids = fields.One2many(
        "pms.board.service.line", "pms_board_service_id"
    )
    pms_property_ids = fields.Many2many(
        "pms.property", string="Properties", required=False, ondelete="restrict"
    )
    pms_board_service_room_type_ids = fields.One2many(
        "pms.board.service.room.type", "pms_board_service_id"
    )
    price_type = fields.Selection(
        [("fixed", "Fixed"), ("percent", "Percent")],
        string="Type",
        default="fixed",
        required=True,
    )
    amount = fields.Float(
        "Amount", digits=("Product Price"), compute="_compute_board_amount", store=True
    )

    # Compute and Search methods
    @api.depends("board_service_line_ids.amount")
    def _compute_board_amount(self):
        for record in self:
            total = 0
            for service in record.board_service_line_ids:
                total += service.amount
            record.update({"amount": total})
