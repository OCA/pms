# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

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
    invoice_to_agency = fields.Selection(
        string="Invoice Agency",
        help="Indicates if agency invoices partner",
        selection=[
            ("never", "Never"),
            ("manual", "Manual"),
            ("always", "Always"),
        ],
        default="never",
        required=True,
    )
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element"
        " if not set, all properties can access",
        required=False,
        comodel_name="pms.property",
        relation="res_partner_pms_property_rel",
        column1="res_partner_id",
        column2="pms_property_id",
        ondelete="restrict",
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
    phone = fields.Char(
        readonly=False,
        store=True,
        compute="_compute_phone",
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
    country_id = fields.Many2one(
        readonly=False,
        store=True,
        compute="_compute_country_id",
    )
    state_id = fields.Many2one(
        readonly=False,
        store=True,
        compute="_compute_state_id",
    )
    city = fields.Char(
        readonly=False,
        store=True,
        compute="_compute_city",
    )
    street = fields.Char(
        readonly=False,
        store=True,
        compute="_compute_street",
    )
    street2 = fields.Char(
        readonly=False,
        store=True,
        compute="_compute_street2",
    )
    zip = fields.Char(
        readonly=False,
        store=True,
        compute="_compute_zip",
    )
    comment = fields.Text(
        tracking=True,
    )
    reservation_possible_customer_id = fields.Many2one(
        string="Possible Customer In Reservation", comodel_name="pms.reservation"
    )
    folio_possible_customer_id = fields.Many2one(
        string="Possible Customer In Folio", comodel_name="pms.folio"
    )
    checkin_partner_possible_customer_id = fields.Many2one(
        string="Possible Customer In Checkin Partner",
        comodel_name="pms.checkin.partner",
    )
    invoicing_policy = fields.Selection(
        string="Invoicing Policy",
        help="""The invoicing policy of the partner,
         set Property to user the policy configured in the Property""",
        selection=[
            ("property", "Property Policy Invoice"),
            ("manual", "Manual"),
            ("checkout", "From Checkout"),
            ("month_day", "Month Day Invoice"),
        ],
        default="property",
    )
    invoicing_month_day = fields.Integer(
        string="Invoicing Month Day",
        help="The day of the month to invoice",
    )
    margin_days_autoinvoice = fields.Integer(
        string="Days from Checkout",
        help="Days from Checkout to generate the invoice",
    )
    residence_street = fields.Char(
        string="Street of residence",
        help="Street of the guest's residence",
        readonly=False,
        store=True,
        compute="_compute_residence_street",
    )
    residence_street2 = fields.Char(
        string="Second street of residence",
        help="Second street of the guest's residence",
        readonly=False,
        store=True,
        compute="_compute_residence_street2",
    )
    residence_zip = fields.Char(
        string="Zip of residence",
        help="Zip of the guest's residence",
        readonly=False,
        store=True,
        compute="_compute_residence_zip",
        change_default=True,
    )
    residence_city = fields.Char(
        string="city of residence",
        help="City of the guest's residence",
        readonly=False,
        store=True,
        compute="_compute_residence_city",
    )
    residence_country_id = fields.Many2one(
        string="Country of residence",
        help="Partner country of residence",
        readonly=False,
        store=True,
        compute="_compute_residence_country_id",
        comodel_name="res.country",
    )
    residence_state_id = fields.Many2one(
        string="State of residence",
        help="Partner state of residence",
        readonly=False,
        store=True,
        compute="_compute_residence_state_id",
        comodel_name="res.country.state",
    )

    @api.depends("pms_checkin_partner_ids", "pms_checkin_partner_ids.gender")
    def _compute_gender(self):
        if hasattr(super(), "_compute_gender"):
            super()._compute_gender()
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
            super()._compute_birthdate_date()
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
            super()._compute_nationality_id()
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

    @api.depends("pms_checkin_partner_ids", "pms_checkin_partner_ids.phone")
    def _compute_phone(self):
        if hasattr(super(), "_compute_phone"):
            super()._compute_phone()
        for record in self:
            if not record.phone and record.pms_checkin_partner_ids:
                phone = list(
                    filter(None, set(record.pms_checkin_partner_ids.mapped("phone")))
                )
                if len(phone) == 1:
                    record.phone = phone[0]
                else:
                    record.phone = False
            elif not record.phone:
                record.phone = False

    @api.depends("pms_checkin_partner_ids", "pms_checkin_partner_ids.residence_street")
    def _compute_residence_street(self):
        if hasattr(super(), "_compute_residence_street"):
            super()._compute_residence_street()
        for record in self:
            if not record.residence_street and record.pms_checkin_partner_ids:
                residence_street = list(
                    filter(
                        None,
                        set(record.pms_checkin_partner_ids.mapped("residence_street")),
                    )
                )
                if len(residence_street) == 1:
                    record.residence_street = residence_street[0]
                else:
                    record.residence_street = False
            elif not record.residence_street:
                record.residence_street = False

    @api.depends("pms_checkin_partner_ids", "pms_checkin_partner_ids.residence_street2")
    def _compute_residence_street2(self):
        if hasattr(super(), "_compute_residence_street2"):
            super()._compute_residence_street2()
        for record in self:
            if not record.residence_street2 and record.pms_checkin_partner_ids:
                residence_street2 = list(
                    filter(
                        None,
                        set(record.pms_checkin_partner_ids.mapped("residence_street2")),
                    )
                )
                if len(residence_street2) == 1:
                    record.residence_street2 = residence_street2[0]
                else:
                    record.residence_street2 = False
            elif not record.residence_street2:
                record.residence_street2 = False

    @api.depends("pms_checkin_partner_ids", "pms_checkin_partner_ids.residence_zip")
    def _compute_residence_zip(self):
        if hasattr(super(), "_compute_residence_zip"):
            super()._compute_residence_zip()
        for record in self:
            if not record.residence_zip and record.pms_checkin_partner_ids:
                residence_zip = list(
                    filter(
                        None,
                        set(record.pms_checkin_partner_ids.mapped("residence_zip")),
                    )
                )
                if len(residence_zip) == 1:
                    record.residence_zip = residence_zip[0]
                else:
                    record.residence_zip = False
            elif not record.residence_zip:
                record.residence_zip = False

    @api.depends("pms_checkin_partner_ids", "pms_checkin_partner_ids.residence_city")
    def _compute_residence_city(self):
        if hasattr(super(), "_compute_residence_city"):
            super()._compute_residence_city()
        for record in self:
            if not record.residence_city and record.pms_checkin_partner_ids:
                residence_city = list(
                    filter(
                        None,
                        set(record.pms_checkin_partner_ids.mapped("residence_city")),
                    )
                )
                if len(residence_city) == 1:
                    record.residence_city = residence_city[0]
                else:
                    record.residence_city = False
            elif not record.residence_city:
                record.residence_city = False

    @api.depends(
        "pms_checkin_partner_ids",
        "pms_checkin_partner_ids.residence_country_id",
        "nationality_id",
    )
    def _compute_residence_country_id(self):
        if hasattr(super(), "_compute_residence_country_id"):
            super()._compute_residence_country_id()
        for record in self:
            if not record.residence_country_id and record.pms_checkin_partner_ids:
                residence_country_id = list(
                    filter(
                        None,
                        set(
                            record.pms_checkin_partner_ids.mapped(
                                "residence_country_id"
                            )
                        ),
                    )
                )
                if len(residence_country_id) == 1:
                    record.residence_country_id = residence_country_id[0]
                else:
                    record.residence_country_id = False
            elif not record.residence_country_id and record.nationality_id:
                record.residence_country_id = record.nationality_id
            elif not record.residence_country_id:
                record.residence_country_id = False

    @api.depends(
        "pms_checkin_partner_ids", "pms_checkin_partner_ids.residence_state_id"
    )
    def _compute_residence_state_id(self):
        if hasattr(super(), "_compute_residence_state_id"):
            super()._compute_residence_state_id()
        for record in self:
            if not record.residence_state_id and record.pms_checkin_partner_ids:
                residence_state_id = list(
                    filter(
                        None,
                        set(
                            record.pms_checkin_partner_ids.mapped("residence_state_id")
                        ),
                    )
                )
                if len(residence_state_id) == 1:
                    record.residence_state_id = residence_state_id[0]
                else:
                    record.residence_state_id = False
            elif not record.residence_state_id:
                record.residence_state_id = False

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
            super()._compute_email()
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
            super()._compute_mobile()
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
            super()._compute_firstname()
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
            super()._compute_lastname()
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
            super()._compute_lastname2()
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

    @api.depends("residence_country_id")
    def _compute_country_id(self):
        if hasattr(super(), "_compute_country_id"):
            super()._compute_country_id()
        for record in self:
            if (
                not record.parent_id
                and not record.country_id
                and record.residence_country_id
            ):
                record.country_id = record.residence_country_id
            elif not record.country_id:
                record.country_id = False

    @api.depends("residence_state_id")
    def _compute_state_id(self):
        if hasattr(super(), "_compute_state_id"):
            super()._compute_state_id()
        for record in self:
            if (
                not record.parent_id
                and not record.state_id
                and record.residence_state_id
            ):
                record.state_id = record.residence_state_id
            elif not record.state_id:
                record.state_id = False

    @api.depends("residence_city")
    def _compute_city(self):
        if hasattr(super(), "_compute_city"):
            super()._compute_city()
        for record in self:
            if not record.parent_id and not record.city and record.residence_city:
                record.city = record.residence_city
            elif not record.city:
                record.city = False

    @api.depends("residence_street")
    def _compute_street(self):
        if hasattr(super(), "_compute_street"):
            super()._compute_street()
        for record in self:
            if not record.parent_id and not record.street and record.residence_street:
                record.street = record.residence_street
            elif not record.street:
                record.street = False

    @api.depends("residence_street2")
    def _compute_street2(self):
        if hasattr(super(), "_compute_street2"):
            super()._compute_street2()
        for record in self:
            if not record.parent_id and not record.street2 and record.residence_street2:
                record.street2 = record.residence_street2
            elif not record.street2:
                record.street2 = False

    @api.depends("residence_zip")
    def _compute_zip(self):
        if hasattr(super(), "_compute_zip"):
            super()._compute_zip()
        for record in self:
            if not record.parent_id and not record.zip and record.residence_zip:
                record.zip = record.residence_zip
            elif not record.zip:
                record.zip = False

    def _compute_reservations_count(self):
        # Return reservation with partner included in reservation and/or checkin
        pms_reservation_obj = self.env["pms.reservation"]
        for record in self:
            checkin_reservation_ids = (
                self.env["pms.checkin.partner"]
                .search([("partner_id", "=", record.id)])
                .mapped("reservation_id.id")
            )
            record.reservations_count = pms_reservation_obj.search_count(
                [
                    "|",
                    (
                        "partner_id.id",
                        "child_of",
                        record.id if isinstance(record.id, int) else False,
                    ),
                    ("id", "in", checkin_reservation_ids),
                ]
            )

    def action_partner_reservations(self):
        self.ensure_one()
        checkin_reservation_ids = (
            self.env["pms.checkin.partner"]
            .search([("partner_id", "=", self.id)])
            .mapped("reservation_id.id")
        )
        reservations = self.env["pms.reservation"].search(
            [
                "|",
                (
                    "partner_id.id",
                    "child_of",
                    self.id if isinstance(self.id, int) else False,
                ),
                ("id", "in", checkin_reservation_ids),
            ]
        )
        action = self.env["ir.actions.actions"]._for_xml_id(
            "pms.open_pms_reservation_form_tree_all"
        )
        if len(reservations) > 1:
            action["domain"] = [("id", "in", reservations.ids)]
        elif len(reservations) == 1:
            form_view = [(self.env.ref("pms.pms_reservation_view_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = reservations.id
        else:
            action = {"type": "ir.actions.act_window_close"}

        if len(self) == 1:
            context = {
                "default_partner_id": self.id,
                "default_user_id": self.user_id.id,
            }
            action["context"] = context
        return action

    def _compute_folios_count(self):
        # Return folios count with partner included in folio and/or folio checkins
        pms_folio_obj = self.env["pms.folio"]
        for record in self:
            checkin_folio_ids = (
                self.env["pms.checkin.partner"]
                .search([("partner_id", "=", record.id)])
                .mapped("folio_id.id")
            )
            record.folios_count = pms_folio_obj.search_count(
                [
                    "|",
                    (
                        "partner_id.id",
                        "=",
                        record.id if isinstance(record.id, int) else False,
                    ),
                    ("id", "in", checkin_folio_ids),
                ]
            )

    def action_partner_folios(self):
        self.ensure_one()
        checkin_folio_ids = (
            self.env["pms.checkin.partner"]
            .search([("partner_id", "=", self.id)])
            .mapped("folio_id.id")
        )
        folios = self.env["pms.folio"].search(
            [
                "|",
                (
                    "partner_id.id",
                    "child_of",
                    self.id if isinstance(self.id, int) else False,
                ),
                ("id", "in", checkin_folio_ids),
            ]
        )
        action = self.env["ir.actions.actions"]._for_xml_id(
            "pms.open_pms_folio1_form_tree_all"
        )
        if len(folios) > 1:
            action["domain"] = [("id", "in", folios.ids)]
        elif len(folios) == 1:
            form_view = [(self.env.ref("pms.pms_folio_view_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = folios.id
        else:
            action = {"type": "ir.actions.act_window_close"}

        if len(self) == 1:
            context = {
                "default_partner_id": self.id,
                "default_user_id": self.user_id.id,
            }
            action["context"] = context
        return action

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

    def _check_enought_invoice_data(self):
        self.ensure_one()
        # Template to be inherited by localization modules
        return True

    def unlink(self):
        dummy, various_partner_id = self.env["ir.model.data"].get_object_reference(
            "pms", "various_pms_partner"
        )
        if various_partner_id in self.ids:
            various_partner = self.browse(various_partner_id)
            raise ValidationError(
                _("The partner %s cannot be deleted"), various_partner.name
            )
        return super().unlink()

    def create(self, vals):
        check_missing_document = self._check_document_partner_required(vals)
        if check_missing_document:
            raise ValidationError(_("A document identification is required"))

        return super().create(vals)

    def write(self, vals):
        check_missing_document = self._check_document_partner_required(
            vals, partners=self
        )
        if check_missing_document:
            # REVIEW: Deactivate this check for now, because it can generate problems
            # with other modules that update technical partner fields
            _logger.warning(
                _("Partner without document identification, update vals %s"), vals
            )
            # We only check if the vat or document_number is updated
            if "vat" in vals or "document_number" in vals:
                raise ValidationError(_("A document identification is required"))
        return super().write(vals)

    @api.model
    def _check_document_partner_required(self, vals, partners=False):
        company_ids = (
            self.env["res.company"].sudo().search([]).ids
            if (not partners or any([not partner.company_id for partner in partners]))
            else partners.mapped("company_id.id")
        )
        if not self.env.context.get("avoid_document_restriction") and any(
            [
                self.env["res.company"].browse(company_id).document_partner_required
                for company_id in company_ids
            ]
        ):
            return self._missing_document(vals, partners)
        return False

    @api.model
    def _missing_document(self, vals, partners=False):
        if (
            vals.get("vat") is False
            or vals.get("vat") == ""
            or (
                "vat" not in vals
                and (
                    any([not partner.vat for partner in partners]) if partners else True
                )
            )
        ):
            return True
        return False

    @api.constrains("is_agency", "property_product_pricelist")
    def _check_agency_pricelist(self):
        if any(
            record.is_agency and not record.property_product_pricelist.is_pms_available
            for record in self
        ):
            raise models.ValidationError(
                _(
                    """
                    Agency must have a PMS pricelist, please review the
                    pricelists configuration (%s) to allow it for PMS,
                    or the pricelist selected for the agencies: %s
                    """
                )
                % (
                    ",".join(self.mapped("property_product_pricelist.name")),
                    "".join(self.mapped("name")),
                )
            )
