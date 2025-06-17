from odoo import api, fields, models


class IrPmsProperty(models.Model):
    _name = "ir.pms.property"
    _description = "IrPmsProperty"

    pms_property_id = fields.Many2one(
        string="Properties",
        help="",
        comodel_name="pms.property",
        index=True,
    )
    model_id = fields.Many2one(string="Model", comodel_name="ir.model", index=True)
    field_id = fields.Many2one(
        string="Field",
        comodel_name="ir.model.fields",
        index=True,
    )
    record = fields.Integer(string="Record Id")
    value_integer = fields.Integer(string="Integer Field Value")
    value_float = fields.Float(string="Float Field Value")
    value_reference = fields.Text(string="Reference Field Value")
    model_name = fields.Char(
        compute="_compute_model_name",
        store=True,
        readonly=False,
    )
    field_name = fields.Char(
        compute="_compute_field_name",
        store=True,
        readonly=False,
    )

    def get_field_value(
        self, pms_property_id, model_name, field_name, record_id, value_type
    ):
        model = self.env["ir.model"].search([("model", "=", model_name)])
        if model:
            field_id = self.env["ir.model.fields"].search(
                [("name", "=", field_name), ("model_id", "=", model.id)]
            )
            ir_pms_property = self.env["ir.pms.property"].search(
                [
                    ("pms_property_id", "=", pms_property_id),
                    ("field_id", "=", field_id[0].id),
                    ("record", "=", record_id),
                ]
            )
            if ir_pms_property:
                if value_type is int:
                    value = ir_pms_property.value_integer
                elif value_type is float:
                    value = ir_pms_property.value_float
                else:
                    index_bracket = ir_pms_property.value_reference.index("(")
                    index_comma = ir_pms_property.value_reference.index(",")
                    model_name = ir_pms_property.value_reference[:index_bracket]
                    resource_id = ir_pms_property.value_reference[
                        index_bracket + 1 : index_comma
                    ]
                    value = self.env[model_name].browse(int(resource_id))
                return value
            return False

    def set_field_value(
        self, pms_property_id, model_name, field_name, record_id, value
    ):
        model = self.env["ir.model"].search([("model", "=", model_name)])
        if model:
            field_id = self.env["ir.model.fields"].search(
                [("name", "=", field_name), ("model_id", "=", model.id)]
            )
            ir_pms_property = self.env["ir.pms.property"].search(
                [
                    ("pms_property_id", "=", pms_property_id),
                    ("field_id", "=", field_id[0].id),
                    ("record", "=", record_id),
                ]
            )
            if isinstance(value, int):
                value_type = "value_integer"
            elif isinstance(value, float):
                value_type = "value_float"
            else:
                value_type = "value_reference"
                value = str(value)
            if ir_pms_property:
                ir_pms_property.write(
                    {
                        value_type: value,
                    }
                )
            else:
                self.env["ir.pms.property"].create(
                    {
                        "pms_property_id": pms_property_id,
                        "model_id": model.id,
                        "field_id": field_id[0].id,
                        value_type: value,
                        "record": record_id,
                    }
                )

    @api.depends("model_id")
    def _compute_model_name(self):
        for record in self:
            record.model_name = record.model_id.model

    @api.depends("field_id")
    def _compute_field_name(self):
        for record in self:
            record.field_name = record.field_id.name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "model_id" not in vals and "model_name" in vals:
                model_id = self.env["ir.model"].search(
                    [("model", "=", vals["model_name"])]
                )
                vals.update(
                    {
                        "model_id": model_id.id,
                    }
                )
            if "field_id" not in vals and "field_name" in vals:
                field_id = self.env["ir.model.fields"].search(
                    [
                        ("name", "=", vals["field_name"]),
                        ("model_id", "=", vals["model_id"]),
                    ]
                )
                vals.update(
                    {
                        "field_id": field_id.id,
                    }
                )
        return super().create(vals)
