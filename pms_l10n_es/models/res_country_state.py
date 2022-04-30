from odoo import _, api, fields, models


class ResCountryState(models.Model):
    _inherit = "res.country.state"

    ine_code = fields.Char(string="INE State Code")

    @api.constrains("ine_code")
    def _check_ine_code(self):
        for record in self:
            if record.country_id.code == "ES" and not record.ine_code:
                raise models.ValidationError(
                    _(
                        "The state %s of %s must have an INE code"
                        % (record.name, record.country_id.name)
                    )
                )
