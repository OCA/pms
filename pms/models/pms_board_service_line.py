# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsBoardServiceLine(models.Model):
    _name = "pms.board.service.line"
    _description = "Services on Board Service included"
    _check_pms_properties_auto = True

    pms_board_service_id = fields.Many2one(
        string="Board Service",
        help="Board Service in which this line is included",
        required=True,
        index=True,
        comodel_name="pms.board.service",
        ondelete="cascade",
        check_pms_properties=True,
    )
    product_id = fields.Many2one(
        string="Product",
        help="Product associated with this board service line",
        required=True,
        index=True,
        comodel_name="product.product",
        check_pms_properties=True,
    )
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        comodel_name="pms.property",
        relation="pms_board_service_line_pms_property_rel",
        column1="pms_board_service_line_id",
        column2="pms_property_id",
        store=True,
        check_pms_properties=True,
    )
    amount = fields.Float(
        help="Price for this Board Service Line/Product",
        default=lambda self: self._get_default_price(),
        digits=("Product Price"),
    )
    adults = fields.Boolean(
        help="Apply service to adults",
        default=False,
    )
    children = fields.Boolean(
        help="Apply service to children",
        default=False,
    )

    def _get_default_price(self):
        if self.product_id:
            return self.product_id.list_price

    @api.onchange("product_id")
    def onchange_product_id(self):
        if self.product_id:
            self.update({"amount": self.product_id.list_price})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            properties = False
            if "pms_board_service_id" in vals:
                board_service = self.env["pms.board.service"].browse(
                    vals["pms_board_service_id"]
                )
                properties = board_service.pms_property_ids
            if properties:
                vals.update(
                    {
                        "pms_property_ids": properties,
                    }
                )
        return super().create(vals_list)

    def write(self, vals):
        properties = False
        if "pms_board_service_id" in vals:
            board_service = self.env["pms.board.service"].browse(
                vals["pms_board_service_id"]
            )
            properties = board_service.pms_property_ids
        if properties:
            vals.update(
                {
                    "pms_property_ids": properties,
                }
            )
        return super().write(vals)

    @api.constrains("adults", "children")
    def _check_adults_children(self):
        for record in self:
            if not record.adults and not record.children:
                raise ValidationError(_("Adults or Children must be checked"))
