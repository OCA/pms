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
        inverse="_inverse_daily_limit",
    )
    list_price = fields.Float(
        compute="_compute_list_price",
        inverse="_inverse_list_price",
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

    @api.depends_context("allowed_pms_property_ids")
    # @api.depends("pms_property_ids")
    def _compute_daily_limit(self):
        for record in self:
            pms_property_id = self.env.user.get_active_property_ids()[0]
            if pms_property_id:
                model_id = self.env["ir.model"].browse(self._name).id
                model = self.env["ir.model"].search([("model", "=", model_id)])
                if model:
                    field_id = self.env["ir.model.fields"].search(
                        [("name", "=", "daily_limit"), ("model_id", "=", model.id)]
                    )
                    ir_pms_property = self.env["ir.pms.property"].search(
                        [
                            ("pms_property_id", "=", pms_property_id),
                            ("field_id", "=", field_id[0].id),
                            ("record", "=", record.id),
                        ]
                    )
                    if ir_pms_property:
                        record.daily_limit = ir_pms_property.value_integer
                    else:
                        record.daily_limit = False

    @api.depends_context("allowed_pms_property_ids")
    # @api.depends("pms_property_ids")
    def _compute_list_price(self):
        for record in self:
            pms_property_id = self.env.user.get_active_property_ids()[0]
            if pms_property_id:
                model_id = self.env["ir.model"].browse(self._name).id
                model = self.env["ir.model"].search([("model", "=", model_id)])
                if model:
                    field_id = self.env["ir.model.fields"].search(
                        [("name", "=", "list_price"), ("model_id", "=", model.id)]
                    )
                    ir_pms_property = self.env["ir.pms.property"].search(
                        [
                            ("pms_property_id", "=", pms_property_id),
                            ("field_id", "=", field_id[0].id),
                            ("record", "=", record.id),
                        ]
                    )
                    if ir_pms_property:
                        record.list_price = ir_pms_property.value_float

    def _inverse_daily_limit(self):
        for record in self:
            pms_property_id = self.env.user.get_active_property_ids()[0]
            if pms_property_id:
                model_id = self.env["ir.model"].browse(self._name).id
                model = self.env["ir.model"].search([("model", "=", model_id)])
                if model:
                    field_id = self.env["ir.model.fields"].search(
                        [("name", "=", "daily_limit"), ("model_id", "=", model.id)]
                    )
                    ir_pms_property = self.env["ir.pms.property"].search(
                        [
                            ("pms_property_id", "=", pms_property_id),
                            ("field_id", "=", field_id[0].id),
                            ("record", "=", record.id),
                        ]
                    )
                    if ir_pms_property:
                        ir_pms_property.value_integer = record.daily_limit
                    else:
                        self.env["ir.pms.property"].create(
                            {
                                "pms_property_id": pms_property_id,
                                "model_id": model.id,
                                "field_id": field_id[0].id,
                                "value_integer": record.daily_limit,
                                "record": record.id,
                            }
                        )

    def _inverse_list_price(self):
        for record in self:
            pms_property_id = self.env.user.get_active_property_ids()[0]
            if pms_property_id:
                model_id = self.env["ir.model"].browse(self._name).id
                model = self.env["ir.model"].search([("model", "=", model_id)])
                if model:
                    field_id = self.env["ir.model.fields"].search(
                        [("name", "=", "list_price"), ("model_id", "=", model.id)]
                    )
                    ir_pms_property = self.env["ir.pms.property"].search(
                        [
                            ("pms_property_id", "=", pms_property_id),
                            ("field_id", "=", field_id[0].id),
                            ("record", "=", record.id),
                        ]
                    )
                    if ir_pms_property:
                        ir_pms_property.value_float = record.list_price
                    else:
                        self.env["ir.pms.property"].create(
                            {
                                "pms_property_id": pms_property_id,
                                "model_id": model.id,
                                "field_id": field_id[0].id,
                                "value_float": record.list_price,
                                "record": record.id,
                            }
                        )
