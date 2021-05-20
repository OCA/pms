from odoo import api, fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    institution = fields.Selection(
        [
            ("guardia_civil", "Guardia Civil"),
            ("policia_nacional", "Policía Nacional (soon)"),
            ("ertxaintxa", "Ertxaintxa (soon)"),
            ("mossos", "Mossos_d'esquadra (soon)"),
        ],
        string="Institution",
        default="guardia_civil",
        help="Institution to send daily guest data.",
    )
    institution_property_id = fields.Char(
        string="Institution property id",
        size=10,
        help="Id provided by institution to send data from property.",
    )
    institution_user = fields.Char(
        string="Institution user", help="User provided by institution to send the data."
    )
    institution_password = fields.Char(
        string="Institution password",
        help="Password provided by institution to send the data.",
    )
    sequence_id = fields.Many2one("ir.sequence")

    # ORM Overrides
    @api.model
    def create(self, vals):
        result = super(PmsProperty, self).create(vals)
        result["sequence_id"] = self.env["ir.sequence"].create(
            {
                "name": "sequence for property: " + result["name"],
                "code": "property." + str(result.id),
                "padding": 3,
            }
        )
        return result

    def write(self, vals):
        result = super(PmsProperty, self).write(vals)
        for record in self:
            if not record.sequence_id:
                record.sequence_id = self.env["ir.sequence"].create(
                    {
                        "name": "sequence for property: " + result["name"],
                        "code": "property." + str(result.id),
                        "padding": 3,
                    }
                )
        return result
