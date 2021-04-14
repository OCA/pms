# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsBoardServiceLine(models.Model):
    _name = "pms.board.service.line"
    _description = "Services on Board Service included"

    pms_board_service_id = fields.Many2one(
        string="Board Service",
        help="Board Service in which this line is included",
        required=True,
        comodel_name="pms.board.service",
        ondelete="cascade",
    )
    product_id = fields.Many2one(
        string="Product",
        help="Product associated with this board service line",
        required=True,
        comodel_name="product.product",
    )
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        comodel_name="pms.property",
        related="pms_board_service_id.pms_property_ids",
    )
    amount = fields.Float(
        string="Amount",
        help="Price for this Board Service Line/Product",
        default=lambda self: self._get_default_price(),
        digits=("Product Price"),
    )

    def _get_default_price(self):
        if self.product_id:
            return self.product_id.list_price

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            self.update({"amount": self.product_id.list_price})

    @api.constrains("pms_property_ids", "product_id")
    def _check_property_integrity(self):
        for record in self:
            if record.pms_property_ids and record.product_id.pms_property_ids:
                for pms_property in record.pms_property_ids:
                    if pms_property not in record.product_id.pms_property_ids:
                        raise ValidationError(_("Property not allowed in product"))
