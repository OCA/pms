from odoo import fields, models


class IrPmsProperty(models.Model):
    _name = "ir.pms.property"

    pms_property_id = fields.Many2one(string="Properties", comodel_name="pms.property")

    model_id = fields.Many2one(string="Model", comodel_name="ir.model")

    field_id = fields.Many2one(string="Field", comodel_name="ir.model.fields")

    value = fields.Integer(string="Field Value")
