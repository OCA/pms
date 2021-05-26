from odoo import api, fields, models


class PmsCheckinPartner(models.Model):
    _inherit = "pms.checkin.partner"

    firstname = fields.Char(
        "First Name",
        compute="_compute_firstname",
        store=True,
        readonly=False,
    )
    lastname = fields.Char(
        "Last Name",
        compute="_compute_lastname",
        store=True,
        readonly=False,
    )
    lastname2 = fields.Char(
        "Second Last Name",
        compute="_compute_lastname2",
        store=True,
        readonly=False,
    )
    birthdate_date = fields.Date(
        "Birthdate",
        compute="_compute_birth_date",
        store=True,
        readonly=False,
    )
    document_number = fields.Char(
        "Document Number",
        compute="_compute_document_number",
        store=True,
        readonly=False,
    )
    document_type = fields.Selection(
        [
            ("D", "DNI"),
            ("P", "Passport"),
            ("C", "Driving License"),
            ("I", "Identification Document"),
            ("N", "Spanish residence permit"),
            ("X", "European residence permit"),
        ],
        string="Document Type",
        help="Select a valid document type",
        compute="_compute_document_type",
        store=True,
        readonly=False,
    )
    document_expedition_date = fields.Date(
        "Expedition Date",
        compute="_compute_document_expedition_date",
        store=True,
        readonly=False,
    )
    gender = fields.Selection(
        [("male", "Male"), ("female", "Female"), ("other", "Other")],
        string="Gender",
        compute="_compute_gender",
        store=True,
        readonly=False,
    )

    @api.depends("partner_id", "partner_id.lastname")
    def _compute_lastname(self):
        for record in self:
            if not record.lastname:
                record.lastname = record.partner_id.lastname

    @api.depends("partner_id", "partner_id.firstname")
    def _compute_firstname(self):
        for record in self:
            if not record.firstname:
                record.firstname = record.partner_id.firstname

    @api.depends("partner_id", "partner_id.lastname2")
    def _compute_lastname2(self):
        for record in self:
            if not record.lastname2:
                record.lastname2 = record.partner_id.lastname2

    @api.depends("partner_id", "partner_id.birthdate_date")
    def _compute_birth_date(self):
        for record in self:
            if not record.birthdate_date:
                record.birthdate_date = record.partner_id.birthdate_date

    @api.depends("partner_id", "partner_id.document_number")
    def _compute_document_number(self):
        for record in self:
            if not record.document_number:
                record.document_number = record.partner_id.document_number

    @api.depends("partner_id", "partner_id.document_type")
    def _compute_document_type(self):
        for record in self:
            if not record.document_type:
                record.document_type = record.partner_id.document_type

    @api.depends("partner_id", "partner_id.document_expedition_date")
    def _compute_document_expedition_date(self):
        for record in self:
            if not record.document_expedition_date:
                record.document_expedition_date = (
                    record.partner_id.document_expedition_date
                )

    @api.depends("partner_id", "partner_id.gender")
    def _compute_gender(self):
        for record in self:
            if not record.gender:
                record.gender = record.partner_id.gender

    @api.model
    def _checkin_mandatory_fields(self, depends=False):
        mandatory_fields = super(PmsCheckinPartner, self)._checkin_mandatory_fields(
            depends
        )
        mandatory_fields.extend(
            [
                "lastname2",
                "birthdate_date",
                "document_number",
                "document_type",
                "document_expedition_date",
                "gender",
            ]
        )
        return mandatory_fields
