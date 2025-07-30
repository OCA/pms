# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsBoardServiceRoomTypeLine(models.Model):
    _name = "pms.board.service.room.type.line"
    _description = "Services on Board Service included in Room"
    _check_pms_properties_auto = True

    # Fields declaration
    pms_board_service_room_type_id = fields.Many2one(
        comodel_name="pms.board.service.room.type",
        string="Board Service Room",
        required=True,
        index=True,
        ondelete="cascade",
        help="Board Service Room Type in which this line is included",
    )
    pms_property_id = fields.Many2one(
        comodel_name="pms.property",
        related="pms_board_service_room_type_id.pms_property_id",
        string="Property",
        help="Property with access to the element;"
        " if not set, all properties can access",
        check_pms_properties=True,
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        index=True,
        domain="[('is_pms_available', '=', True)]",
        readonly=True,
        help="Product associated with this board service room type line",
        check_pms_properties=True,
    )
    amount = fields.Float(
        default=lambda self: self._default_amount(),
        digits=("Product Price"),
        help="Price for this Board Service Room Type Line/Product",
    )
    adults = fields.Boolean(
        default=False,
        help="Apply service to adults",
    )
    children = fields.Boolean(
        default=False,
        help="Apply service to children",
    )

    def _default_amount(self):
        return self.product_id.list_price

    @api.constrains("adults", "children")
    def _check_adults_children(self):
        for record in self:
            if not record.adults and not record.children:
                raise ValidationError(_("Adults or Children must be checked"))
