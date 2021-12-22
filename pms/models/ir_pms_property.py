from odoo import fields, models


class IrPmsProperty(models.Model):
    _name = "ir.pms.property"
    _description = "IrPmsProperty"
    pms_property_id = fields.Many2one(string="Properties", comodel_name="pms.property")
    model_id = fields.Many2one(string="Model", comodel_name="ir.model")
    field_id = fields.Many2one(string="Field", comodel_name="ir.model.fields")
    record = fields.Integer(string="Record Id")

    value_integer = fields.Integer(string="Integer Field Value")

    value_float = fields.Float(string="Float Field Value")

    value_reference = fields.Text(string="Reference Field Value")
