# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class PmsBoardServiceRoomTypeLine(models.Model):
    _name = "pms.board.service.room.type.line"
    _description = "Services on Board Service included in Room"
    _check_pms_properties_auto = True

    # Fields declaration
    pms_board_service_room_type_id = fields.Many2one(
        string="Board Service Room",
        help="Board Service Room Type in which this line is included",
        required=True,
        comodel_name="pms.board.service.room.type",
        ondelete="cascade",
    )
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        comodel_name="pms.property",
        relation="pms_board_service_room_type_line_pms_property_rel",
        column1="pms_board_service_room_type_id",
        column2="pms_property_id",
        check_pms_properties=True,
    )
    product_id = fields.Many2one(
        string="Product",
        help="Product associated with this board service room type line",
        comodel_name="product.product",
        readonly=True,
        check_pms_properties=True,
    )
    # TODO def default_amount "amount of service"
    amount = fields.Float(
        string="Amount",
        help="Price for this Board Service Room Type Line/Product",
        default=0.0,
        digits=("Product Price"),
    )

    @api.model
    def create(self, vals):
        properties = False
        if "pms_board_service_room_type_id" in vals:
            board_service = self.env["pms.board.service.room.type"].browse(
                vals["pms_board_service_room_type_id"]
            )
            properties = board_service.pms_property_ids
        if properties:
            vals.update(
                {
                    "pms_property_ids": properties,
                }
            )
        return super(PmsBoardServiceRoomTypeLine, self).create(vals)

    def write(self, vals):
        properties = False
        if "pms_board_service_room_type_id" in vals:
            board_service = self.env["pms.board.service.room.type"].browse(
                vals["pms_board_service_room_type_id"]
            )
            properties = board_service.pms_property_ids
        if properties:
            vals.update(
                {
                    "pms_property_ids": properties,
                }
            )
        return super(PmsBoardServiceRoomTypeLine, self).write(vals)
