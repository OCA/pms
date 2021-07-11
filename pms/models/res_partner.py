# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    reservations_count = fields.Integer(
        string="Number of Reservations",
        help="Number of reservations of the partner",
        compute="_compute_reservations_count",
    )
    folios_count = fields.Integer(
        string="Number of Folios",
        help="Number of folios of the partner",
        compute="_compute_folios_count",
    )
    is_agency = fields.Boolean(
        string="Is Agency", help="Indicates if the partner is an agency"
    )
    sale_channel_id = fields.Many2one(
        string="Sale Channel",
        help="The sale channel of the partner",
        comodel_name="pms.sale.channel",
        domain=[("channel_type", "=", "indirect")],
        ondelete="restrict",
    )
    default_commission = fields.Integer(string="Commission", help="Default commission")
    apply_pricelist = fields.Boolean(
        string="Apply Pricelist",
        help="Indicates if agency pricelist is applied to his reservations",
    )
    invoice_to_agency = fields.Boolean(
        string="Invoice Agency",
        help="Indicates if agency invoices partner",
    )
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        required=False,
        comodel_name="pms.property",
        relation="res_partner_pms_property_rel",
        column1="res_partner_id",
        column2="pms_property_id",
        ondelete="restrict",
        check_pms_properties=True,
    )
    company_id = fields.Many2one(
        check_pms_properties=True,
    )
    pms_checkin_partner_ids = fields.One2many(
        string="Checkin Partners",
        help="Associated checkin partners",
        comodel_name="pms.checkin.partner",
        inverse_name="partner_id",
    )
    pms_reservation_ids = fields.One2many(
        string="Reservations",
        help="Associated reservation",
        comodel_name="pms.reservation",
        inverse_name="partner_id",
    )
    pms_folio_ids = fields.One2many(
        string="Folios",
        help="Associated Folios",
        comodel_name="pms.folio",
        inverse_name="partner_id",
    )
    gender = fields.Selection(
        readonly=False,
        store=True,
        compute="_compute_gender",
    )
    birthdate_date = fields.Date(
        readonly=False,
        store=True,
        compute="_compute_birthdate_date",
    )
    nationality_id = fields.Many2one(
        readonly=False,
        store=True,
        compute="_compute_nationality_id",
    )
    # TODO: Use new partner contact "other or "private" with
    # personal contact address complete??
    # to avoid user country_id on companies contacts.
    # view to checkin partner state_id field
    state_id = fields.Many2one(
        readonly=False,
        store=True,
        compute="_compute_state_id",
    )
    email = fields.Char(
        readonly=False,
        store=True,
        compute="_compute_email",
    )
    mobile = fields.Char(
        readonly=False,
        store=True,
        compute="_compute_mobile",
    )
    firstname = fields.Char(
        readonly=False,
        store=True,
        compute="_compute_firstname",
    )

    lastname = fields.Char(
        readonly=False,
        store=True,
        compute="_compute_lastname",
    )
    lastname2 = fields.Char(
        readonly=False,
        store=True,
        compute="_compute_lastname2",
    )
    comment = fields.Text(
        tracking=True,
    )

    @api.depends("pms_checkin_partner_ids", "pms_checkin_partner_ids.gender")
    def _compute_gender(self):
        if hasattr(super(), "_compute_gender"):
            super()._compute_field()
        for record in self:
            if not record.gender and record.pms_checkin_partner_ids:
                gender = list(
                    filter(None, set(record.pms_checkin_partner_ids.mapped("gender")))
                )
                if len(gender) == 1:
                    record.gender = gender[0]
                else:
                    record.gender = False
            elif not record.gender:
                record.gender = False

    @api.depends("pms_checkin_partner_ids", "pms_checkin_partner_ids.birthdate_date")
    def _compute_birthdate_date(self):
        if hasattr(super(), "_compute_birthdate_date"):
            super()._compute_field()
        for record in self:
            if not record.birthdate_date and record.pms_checkin_partner_ids:
                birthdate = list(
                    filter(
                        None,
                        set(record.pms_checkin_partner_ids.mapped("birthdate_date")),
                    )
                )
                if len(birthdate) == 1:
                    record.birthdate_date = birthdate[0]
                else:
                    record.birthdate_date = False
            elif not record.birthdate_date:
                record.birthdate_date = False

    @api.depends("pms_checkin_partner_ids", "pms_checkin_partner_ids.nationality_id")
    def _compute_nationality_id(self):
        if hasattr(super(), "_compute_nationality_id"):
            super()._compute_field()
        for record in self:
            if not record.nationality_id and record.pms_checkin_partner_ids:
                nationality_id = list(
                    filter(
                        None,
                        set(record.pms_checkin_partner_ids.mapped("nationality_id")),
                    )
                )
                if len(nationality_id) == 1:
                    record.nationality_id = nationality_id[0]
                else:
                    record.nationality_id = False
            elif not record.nationality_id:
                record.nationality_id = False

    @api.depends("pms_checkin_partner_ids", "pms_checkin_partner_ids.state_id")
    def _compute_state_id(self):
        if hasattr(super(), "_compute_state_id"):
            super()._compute_field()
        for record in self:
            if not record.state_id and record.pms_checkin_partner_ids:
                state_id = list(
                    filter(
                        None,
                        set(record.pms_checkin_partner_ids.mapped("state_id")),
                    )
                )
                if len(state_id) == 1:
                    record.state_id = state_id[0]
                else:
                    record.state_id = False
            elif not record.state_id:
                record.state_id = False

    @api.depends(
        "pms_checkin_partner_ids",
        "pms_checkin_partner_ids.email",
        "pms_reservation_ids",
        "pms_reservation_ids.email",
        "pms_folio_ids",
        "pms_folio_ids.email",
    )
    def _compute_email(self):
        if hasattr(super(), "_compute_email"):
            super()._compute_field()
        for record in self:
            if not record.email and (
                record.pms_checkin_partner_ids
                or record.pms_reservation_ids
                or record.pms_folio_ids
            ):
                email = list(
                    filter(
                        None,
                        set(
                            record.pms_checkin_partner_ids.mapped("email")
                            + record.pms_reservation_ids.mapped("email")
                            + record.pms_folio_ids.mapped("email"),
                        ),
                    )
                )
                if len(email) == 1:
                    record.email = email[0]
                else:
                    record.email = False
            elif not record.email:
                record.email = False

    @api.depends(
        "pms_checkin_partner_ids",
        "pms_checkin_partner_ids.mobile",
        "pms_reservation_ids",
        "pms_reservation_ids.mobile",
        "pms_folio_ids",
        "pms_folio_ids.mobile",
    )
    def _compute_mobile(self):
        if hasattr(super(), "_compute_mobile"):
            super()._compute_field()
        for record in self:
            if not record.mobile and (
                record.pms_checkin_partner_ids
                or record.pms_reservation_ids
                or record.pms_folio_ids
            ):
                mobile = list(
                    filter(
                        None,
                        set(
                            record.pms_checkin_partner_ids.mapped("mobile")
                            + record.pms_reservation_ids.mapped("mobile")
                            + record.pms_folio_ids.mapped("mobile"),
                        ),
                    )
                )
                if len(mobile) == 1:
                    record.mobile = mobile[0]
                else:
                    record.mobile = False
            elif not record.mobile:
                record.mobile = False

    @api.depends("pms_checkin_partner_ids", "pms_checkin_partner_ids.firstname")
    def _compute_firstname(self):
        if hasattr(super(), "_compute_firstname"):
            super()._compute_field()
        for record in self:
            if not record.firstname and record.pms_checkin_partner_ids:
                firstname = list(
                    filter(
                        None, set(record.pms_checkin_partner_ids.mapped("firstname"))
                    )
                )
                if len(firstname) == 1:
                    record.firstname = firstname[0]
                else:
                    record.firstname = False
            elif not record.firstname:
                record.firstname = False

    @api.depends("pms_checkin_partner_ids", "pms_checkin_partner_ids.lastname")
    def _compute_lastname(self):
        if hasattr(super(), "_compute_lastname"):
            super()._compute_field()
        for record in self:
            if not record.lastname and record.pms_checkin_partner_ids:
                lastname = list(
                    filter(None, set(record.pms_checkin_partner_ids.mapped("lastname")))
                )
                if len(lastname) == 1:
                    record.lastname = lastname[0]
                else:
                    record.lastname = False
            elif not record.lastname:
                record.lastname = False

    @api.depends("pms_checkin_partner_ids", "pms_checkin_partner_ids.lastname2")
    def _compute_lastname2(self):
        if hasattr(super(), "_compute_lastname2"):
            super()._compute_field()
        for record in self:
            if not record.lastname2 and record.pms_checkin_partner_ids:
                lastname2 = list(
                    filter(
                        None, set(record.pms_checkin_partner_ids.mapped("lastname2"))
                    )
                )
                if len(lastname2) == 1:
                    record.lastname2 = lastname2[0]
                else:
                    record.lastname2 = False
            elif not record.lastname2:
                record.lastname2 = False

    def _compute_reservations_count(self):
        # TODO: recuperar las reservas de los folios del partner
        pms_reservation_obj = self.env["pms.reservation"]
        for record in self:
            record.reservations_count = pms_reservation_obj.search_count(
                [
                    (
                        "partner_id.id",
                        "child_of",
                        record.id if isinstance(record.id, int) else False,
                    )
                ]
            )

    def _compute_folios_count(self):
        pms_folio_obj = self.env["pms.folio"]
        for record in self:
            record.folios_count = pms_folio_obj.search_count(
                [
                    (
                        "partner_id.id",
                        "=",
                        record.id if isinstance(record.id, int) else False,
                    )
                ]
            )

    @api.constrains("is_agency", "sale_channel_id")
    def _check_is_agency(self):
        for record in self:
            if record.is_agency and not record.sale_channel_id:
                raise models.ValidationError(_("Sale Channel must be entered"))
            if record.is_agency and record.sale_channel_id.channel_type != "indirect":
                raise models.ValidationError(
                    _("Sale Channel for an agency must be indirect")
                )
            if not record.is_agency and record.sale_channel_id:
                record.sale_channel_id = None

    # REVIEW: problems with odoo demo data
    # @api.constrains("mobile", "email")
    # def _check_duplicated(self):
    #     for record in self:
    #         partner, field = record._search_duplicated()
    #         if partner:
    #             raise models.ValidationError(
    #                 _(
    #                     "Partner %s found with same %s (%s)",
    #                     partner.name,
    #                     partner._fields[field].string,
    #                     getattr(record, field),
    #                 )
    #             )

    def _search_duplicated(self):
        self.ensure_one()
        partner = False
        for field in self._get_key_fields():
            if getattr(self, field):
                partner = self.search(
                    [(field, "=", getattr(self, field)), ("id", "!=", self.id)]
                )
                if partner:
                    field = field
        return partner, field

    @api.model
    def _get_key_fields(self):
        key_fields = super(ResPartner, self)._get_key_fields()
        key_fields.extend(["document_number"])
        return key_fields
