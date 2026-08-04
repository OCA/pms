from odoo import _, api, fields, models


class ResCountryState(models.Model):
    _inherit = "res.country.state"

    ine_code = fields.Char(string="INE State Code")
    ine_tourism_province_name = fields.Char(
        string="INE Tourism Province Name",
        help="Province literal expected in the PROVINCIA element of the INE "
        "occupancy survey XML files (max. 25 characters), as published in "
        "the INE file specification.",
    )

    @api.constrains("ine_code")
    def _check_ine_code(self):
        for record in self:
            if record.country_id.code == "ES" and not record.ine_code:
                raise models.ValidationError(
                    _("The state {state} of {country} must have an INE code").format(
                        state=record.name, country=record.country_id.name
                    )
                )
