from odoo import _, api, fields, models

# Maximum length of the province literal in the INE survey schemas.
INE_PROVINCE_MAX_LENGTH = 25
# Minimum number of digits the INE survey schemas accept in a phone.
INE_PHONE_MIN_LENGTH = 9


class PmsProperty(models.Model):
    _inherit = "pms.property"

    institution = fields.Selection(
        [
            ("ses", "SES"),
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
    ine_tourism_number = fields.Char(
        "Tourism number",
        help="Registration number in the Ministry of Tourism. Used for INE statistics.",
    )
    ine_seats = fields.Integer(
        string="Beds available excluding extra beds",
        default=0,
        help="Used for INE statistics.",
    )
    ine_permanent_staff = fields.Integer(
        string="Permanent Staff", default=0, help="Used for INE statistics."
    )
    ine_eventual_staff = fields.Integer(
        string="Eventual Staff", default=0, help="Used for INE statistics."
    )
    ine_unpaid_staff = fields.Integer(
        string="Unpaid Staff", default=0, help="Used for INE statistics."
    )
    ine_category_id = fields.Many2one(
        comodel_name="pms.ine.tourism.type.category",
        help="Hotel category in the Ministry of Tourism. Used for INE statistics.",
    )
    ine_order_number = fields.Char(
        string="INE Order Number",
        help="Order number of the INE questionnaire (11 characters). It is "
        "fixed for each establishment, so it is kept here to submit the "
        "questionnaire. The control code, on the contrary, changes with "
        "every questionnaire and is single use, so it is never stored.",
    )
    ine_informant_name = fields.Char(
        string="INE Informant Name",
        help="Contact person reported in the INFORMANTE block of the INE "
        "Tourist Apartments Occupancy Survey (EOAP).",
    )
    ine_informant_job = fields.Char(
        string="INE Informant Job Position",
        help="Job position of the INE informant (EOAP).",
    )
    ine_informant_phone = fields.Char(
        string="INE Informant Phone",
        help="Phone of the INE informant (EOAP). If empty, the property "
        "phone is used.",
    )
    ine_informant_email = fields.Char(
        string="INE Informant Email",
        help="Email of the INE informant (EOAP).",
    )
    spanish_tourism_classification_id = fields.Many2one(
        comodel_name="pms.tourism.classification",
        string="Spanish Tourism Classification",
        help="Spanish tourism classification.",
    )
    ine_ready = fields.Boolean(
        string="Ready for the INE survey",
        compute="_compute_ine_ready",
        help="Whether the property has everything the INE occupancy survey "
        "needs. When it has not, the missing data is listed in the INE "
        "configuration warnings.",
    )
    ine_blocking_reasons = fields.Text(
        string="INE Configuration Warnings",
        compute="_compute_ine_ready",
        help="What is missing before the INE occupancy survey can be built.",
    )

    @api.depends(
        "name",
        "street",
        "zip",
        "city",
        "phone",
        "company_id.name",
        "company_id.vat",
        "partner_id.state_id",
        "ine_tourism_number",
        "ine_category_id",
        "ine_seats",
        "ine_informant_name",
        "ine_informant_job",
        "ine_informant_email",
    )
    def _compute_ine_ready(self):
        for record in self:
            problems = record.ine_configuration_problems()
            record.ine_ready = not problems
            record.ine_blocking_reasons = "\n".join(problems)

    def ine_configuration_problems(self):
        """List what keeps the property from reporting to the INE.

        Returned as plain sentences so that both the wizard and the app can
        show them: a survey rejected for a missing field is the most common
        support request around the INE, and the establishment can only act
        on it when it is told which field it is.
        """
        self.ensure_one()
        problems = []
        if not self.name:
            problems.append(_("The property name is not established."))
        if not self.company_id.vat:
            problems.append(_("The company VAT is not established."))
        if not self.company_id.name:
            problems.append(_("The company name is not established."))
        if not self.ine_tourism_number:
            problems.append(_("The property tourism number is not established."))
        if not self.street:
            problems.append(_("The property street is not established."))
        if not self.zip:
            problems.append(_("The property zip is not established."))
        if not self.city:
            problems.append(_("The property city is not established."))
        if not self.partner_id.state_id:
            problems.append(_("The property state is not established."))
        if not self.phone:
            problems.append(_("The property phone is not established."))
        elif len(self.phone.replace(" ", "")) < INE_PHONE_MIN_LENGTH:
            problems.append(
                _(
                    "The property phone '%s' is too short: the INE survey "
                    "requires at least 9 digits.",
                    self.phone,
                )
            )
        if not self.ine_category_id:
            problems.append(_("The property category is not established."))
        province = (
            self.partner_id.state_id.ine_tourism_province_name
            or self.partner_id.state_id.name
        )
        if province and len(province) > INE_PROVINCE_MAX_LENGTH:
            problems.append(
                _(
                    "The province literal '%s' exceeds the 25 characters "
                    "allowed by the INE survey. Set the 'INE Tourism "
                    "Province Name' field on the property state.",
                    province,
                )
            )
        problems += self._ine_seats_problems()
        if self.ine_category_id.survey_type == "apartments":
            problems += self._ine_informant_problems()
        return problems

    def _ine_seats_problems(self):
        """The declared seats cannot be below what the rooms already offer."""
        seats = sum(
            self.env["pms.room"]
            .search([("in_ine", "=", True), ("pms_property_id", "=", self.id)])
            .mapped("capacity")
        )
        if seats <= self.ine_seats:
            return []
        return [
            _(
                "The rooms reported to the INE add up to %(seats)s seats, "
                "more than the %(declared)s declared in the property. Set "
                "the seats available excluding extra beds.",
                seats=seats,
                declared=self.ine_seats,
            )
        ]

    def _ine_informant_problems(self):
        """The Tourist Apartments survey (EOAP) carries an informant block."""
        problems = []
        if not self.ine_informant_name:
            problems.append(_("The INE informant name is not established."))
        if not self.ine_informant_job:
            problems.append(_("The INE informant job position is not established."))
        if not self.ine_informant_email:
            problems.append(_("The INE informant email is not established."))
        return problems
