# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PmsBoardService(models.Model):
    _name = "pms.board.service"
    _description = "Board Services"

    name = fields.Char(
        string="Board Service Name",
        help="Board Service Name",
        required=True,
        index=True,
        size=64,
        translate=True,
    )
    board_service_line_ids = fields.One2many(
        string="Board Service Lines",
        help="Services included in this Board Service",
        comodel_name="pms.board.service.line",
        inverse_name="pms_board_service_id",
    )
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        required=False,
        comodel_name="pms.property",
        relation="pms_board_service_pms_property_rel",
        column1="board_service_id",
        column2="pms_property_id",
    )
    pms_board_service_room_type_ids = fields.One2many(
        string="Board Services Room Type",
        help="Board Services Room Type corresponding to this Board Service,"
        "One board service for several room types",
        comodel_name="pms.board.service.room.type",
        inverse_name="pms_board_service_id",
    )
    amount = fields.Float(
        string="Amount",
        help="Price for this Board Service. "
        "It corresponds to the sum of his board service lines",
        store=True,
        digits=("Product Price"),
        compute="_compute_board_amount",
    )

    show_detail_report = fields.Boolean(
        string="Show Detail Report",
        help="True if you want that board service detail to be shown on the report",
    )

    @api.depends("board_service_line_ids.amount")
    def _compute_board_amount(self):
        for record in self:
            total = 0
            for service in record.board_service_line_ids:
                total += service.amount
            record.update({"amount": total})
