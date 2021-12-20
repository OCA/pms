# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"
    _check_pms_properties_auto = True

    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        required=False,
        comodel_name="pms.property",
        relation="product_template_pms_property_rel",
        column1="product_tmpl_id",
        column2="pms_property_id",
        ondelete="restrict",
        check_pms_properties=True,
    )
    per_day = fields.Boolean(
        string="Unit increment per day",
        help="Indicates that the product is sold by days",
    )
    per_person = fields.Boolean(
        string="Unit increment per person",
        help="Indicates that the product is sold per person",
    )
    consumed_on = fields.Selection(
        string="Consumed",
        help="Indicates when the product is consumed",
        selection=[("before", "Before night"), ("after", "After night")],
        default="before",
    )
    daily_limit = fields.Integer(
        string="Daily limit",
        help="Indicates how much products can consumed in one day",
        compute="_compute_daily_limit",
        inverse="_inverse_ir_pms_property",
        readonly=False,
        store=True,
    )
    is_extra_bed = fields.Boolean(
        string="Is extra bed",
        help="Indicates if that product is a extra bed, add +1 capacity in the room",
        default=False,
    )
    is_crib = fields.Boolean(
        string="Is a baby crib",
        help="Indicates if that product is a crib",
        default=False,
    )

    # @api.depends_context("allowed_pms_property_ids")
    @api.depends("pms_property_ids")
    def _compute_daily_limit(self):
        for record in self:
            pms_property_id = False
            if record.pms_property_ids:
                pms_property_id = self.env.user.get_active_property_ids()[0]
            if pms_property_id:
                property = self.env["pms.property"].browse(pms_property_id)
            else:
                property = False
            if property:
                model_id = self.env["ir.model"].browse(self._name)
                model = self.env["ir.model"].search([("id", "=", model_id)])
                field_id = self.env["ir.model.fields"].search(
                    [("name", "=", "daily_limit"), ("model_id", "=", model)]
                )
                ir_pms_property = self.env["ir.pms.property"].search(
                    [
                        ("pms_property_id", "=", property.id),
                        ("field_id", "=", field_id.id),
                        ("res_id", "=", record),
                    ]
                )
                record.daily_limit = ir_pms_property.value

    def _inverse_ir_pms_property(self):
        for record in self:
            pms_property_id = self.env.user.get_active_property_ids()[0]
            field_id = self.env["ir.model.fields"].search(
                [("name", "=", "daily_limit")]
            )
            model_id = self.env["ir.model"].search([("field_id", "=", field_id[1].id)])
            ir_pms_property = self.env["ir.pms.property"].search(
                [
                    ("pms_property_id", "=", pms_property_id),
                    ("model_id", "=", model_id.id),
                    ("field_id", "=", field_id[1].id),
                ]
            )
            if ir_pms_property:
                ir_pms_property.value = record.daily_limit
            # else:
            #     crear
