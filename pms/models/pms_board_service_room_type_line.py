# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


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
    pms_property_id = fields.Many2one(
        string="Property",
        help="Property with access to the element;"
        " if not set, all properties can access",
        comodel_name="pms.property",
        check_pms_properties=True,
        related="pms_board_service_room_type_id.pms_property_id",
    )
    product_id = fields.Many2one(
        string="Product",
        help="Product associated with this board service room type line",
        comodel_name="product.product",
        readonly=True,
        check_pms_properties=True,
        domain="[('is_pms_available', '=', True)]",
    )
    amount = fields.Float(
        string="Amount",
        help="Price for this Board Service Room Type Line/Product",
        default=lambda self: self._default_amount(),
        digits=("Product Price"),
    )

    def _default_amount(self):
        return self.product_id.list_price
