from odoo import fields, models

# The INE keeps its own country list for the occupancy surveys, published
# next to the survey schemas. It follows ISO 3166-1 alpha-3 except where ISO
# has no code at all: Kosovo is KOS for the INE and has no alpha-3 in Odoo,
# so its ID_PAIS would come out empty and the file would be rejected by the
# schema. Every other country in Odoo matches the INE list one to one, Spain
# aside, which travels in ID_PROVINCIA_ISLA and is not in their list.
#
# This lives in the code rather than in a data file because the countries of
# the base module carry noupdate, so a CSV row over them is silently ignored.
# The ine_country_code field is left for whatever the INE adds later without
# waiting for a release.
INE_COUNTRY_CODES = {
    "XK": "KOS",
}


class ResCountry(models.Model):
    _inherit = "res.country"

    ine_country_code = fields.Char(
        string="INE Country Code",
        help="Code expected in the ID_PAIS element of the INE occupancy "
        "survey XML files, for the countries the INE does not code as ISO "
        "3166-1 alpha-3 does. Leave it empty to use the alpha-3 code.",
    )

    def ine_get_country_code(self):
        """Return the code the INE expects for the country of residence."""
        self.ensure_one()
        return (
            self.ine_country_code
            or INE_COUNTRY_CODES.get(self.code)
            or self.code_alpha3
        )
