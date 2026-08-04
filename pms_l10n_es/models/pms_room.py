from odoo import fields, models


class PmsRoom(models.Model):
    _inherit = "pms.room"

    in_ine = fields.Boolean(
        help="Take it into account to generate INE statistics",
        default=True,
    )
    ine_apartment_type = fields.Selection(
        selection=[
            ("studio", "Studio"),
            ("apt_2_4", "Apartment 2-4 pax"),
            ("apt_4_6", "Apartment 4-6 pax"),
            ("other", "Other apartments"),
        ],
        help="Accommodation unit typology used by the INE Tourist Apartments "
        "Occupancy Survey (EOAP). Only used when the property reports to "
        "the apartments survey. If empty, it is inferred from the room "
        "capacity (2 pax: studio, up to 4: 2-4 pax, up to 6: 4-6 pax, "
        "bigger: other).",
    )

    def ine_get_apartment_type(self):
        """Return the EOAP typology, inferring it from capacity if unset."""
        self.ensure_one()
        if self.ine_apartment_type:
            return self.ine_apartment_type
        if self.capacity <= 2:
            return "studio"
        if self.capacity <= 4:
            return "apt_2_4"
        if self.capacity <= 6:
            return "apt_4_6"
        return "other"

    institution_independent_account = fields.Boolean(
        string="Independent account for institution (travel reports)",
        help="This room has an independent account",
        default=False,
    )
    institution = fields.Selection(
        [
            ("ses", "SES"),
            ("ertxaintxa", "Ertxaintxa (soon)"),
            ("mossos", "Mossos_d'esquadra (soon)"),
        ],
        help="Institution to send daily guest data.",
        required=False,
    )
    institution_property_id = fields.Char(
        help="Id provided by institution to send data from property.",
    )
    ses_url = fields.Char(
        help="URL to send the data to SES",
    )
    institution_user = fields.Char(
        help="User provided by institution to send the data."
    )
    institution_password = fields.Char(
        help="Password provided by institution to send the data.",
    )
    institution_lessor_id = fields.Char(
        help="Id provided by institution to send data from lessor.",
    )
