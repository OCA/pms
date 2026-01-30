# Copyright 2017  Dario Lodeiros
# Copyright 2018  Alexandre Diaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsCheckinPartner(models.Model):
    _name = "pms.checkin.partner"
    _description = "Partner Checkins"
    _inherit = ["mail.thread", "mail.activity.mixin", "portal.mixin"]
    _rec_name = "identifier"

    identifier = fields.Char(
        help="Checkin Partner Id",
        readonly=True,
        index=True,
        default=lambda self: _("New"),
    )
    partner_id = fields.Many2one(
        string="Partner",
        help="Partner associated with checkin partner",
        index=True,
        comodel_name="res.partner",
        domain="[('is_company', '=', False)]",
    )
    reservation_id = fields.Many2one(
        string="Reservation",
        help="Reservation to which checkin partners belong",
        index=True,
        comodel_name="pms.reservation",
    )
    folio_id = fields.Many2one(
        string="Folio",
        help="Folio to which reservation of checkin partner belongs",
        store=True,
        index=True,
        comodel_name="pms.folio",
        related="reservation_id.folio_id",
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Property to which the folio associated belongs",
        readonly=True,
        store=True,
        index=True,
        comodel_name="pms.property",
        related="reservation_id.pms_property_id",
    )
    name = fields.Char(help="Checkin partner name", related="partner_id.name")
    email = fields.Char(
        string="E-mail",
        help="Checkin Partner Email",
        readonly=False,
        store=True,
        compute="_compute_email",
        inverse=lambda r: r._inverse_partner_fields("email", "email"),
    )
    mobile = fields.Char(
        help="Checkin Partner Mobile",
        readonly=False,
        store=True,
        compute="_compute_mobile",
        inverse=lambda r: r._inverse_partner_fields("mobile", "mobile"),
    )
    phone = fields.Char(
        help="Checkin Partner Phone",
        readonly=False,
        store=True,
        compute="_compute_phone",
        inverse=lambda r: r._inverse_partner_fields("phone", "phone"),
    )
    image_128 = fields.Image(
        string="Image",
        help="Checkin Partner Image, it corresponds with Partner Image associated",
        related="partner_id.image_128",
    )
    segmentation_ids = fields.Many2many(
        string="Segmentation",
        help="Segmentation tags to classify checkin partners",
        readonly=True,
        related="reservation_id.segmentation_ids",
        domain="[('is_used_in_checkin', '=', True)]",
    )
    checkin = fields.Date(
        string="Check in",
        help="Checkin date",
        store=True,
        related="reservation_id.checkin",
        depends=["reservation_id.checkin"],
    )
    checkout = fields.Date(
        string="Check out",
        help="Checkout date",
        store=True,
        related="reservation_id.checkout",
        depends=["reservation_id.checkout"],
    )
    arrival = fields.Datetime("Enter", help="Checkin partner arrival date and time")
    departure = fields.Datetime(
        string="Exit", help="Checkin partner departure date and time"
    )
    state = fields.Selection(
        string="Status",
        help="Status of the checkin partner regarding the reservation",
        readonly=True,
        store=True,
        selection=[
            ("dummy", "Unkown Guest"),
            ("draft", "Incomplete data"),
            ("precheckin", "Pending arrival"),
            ("onboard", "On Board"),
            ("done", "Out"),
            ("cancel", "Cancelled"),
        ],
        compute="_compute_state",
    )

    gender = fields.Selection(
        help="host gender",
        readonly=False,
        store=True,
        compute="_compute_gender",
        selection=[("male", "Male"), ("female", "Female"), ("other", "Other")],
        inverse=lambda r: r._inverse_partner_fields("gender", "gender"),
    )
    nationality_id = fields.Many2one(
        string="Nationality",
        help="host nationality",
        readonly=False,
        store=True,
        index=True,
        compute="_compute_nationality_id",
        comodel_name="res.country",
        inverse=lambda r: r._inverse_partner_fields("nationality_id", "nationality_id"),
    )
    street = fields.Char(
        help="Street of the guest",
        readonly=False,
        store=True,
        compute="_compute_street",
    )
    street2 = fields.Char(
        help="Second street of the guest",
        readonly=False,
        store=True,
        compute="_compute_street2",
    )
    zip = fields.Char(
        help="Zip of the guest",
        readonly=False,
        store=True,
        compute="_compute_zip",
        change_default=True,
    )
    city = fields.Char(
        help="City of the guest",
        readonly=False,
        store=True,
        compute="_compute_city",
    )
    country_id = fields.Many2one(
        string="Country of residence",
        help="Country of the guest",
        readonly=False,
        store=True,
        index=True,
        compute="_compute_country_id",
        comodel_name="res.country",
    )
    state_id = fields.Many2one(
        string="State of residence",
        help="State of the guest",
        readonly=False,
        store=True,
        index=True,
        compute="_compute_state_id",
        comodel_name="res.country.state",
    )

    firstname = fields.Char(
        string="First Name",
        help="host firstname",
        readonly=False,
        store=True,
        compute="_compute_firstname",
        inverse=lambda r: r._inverse_partner_fields("firstname", "firstname"),
    )
    lastname = fields.Char(
        string="Last Name",
        help="host lastname",
        readonly=False,
        store=True,
        compute="_compute_lastname",
        inverse=lambda r: r._inverse_partner_fields("lastname", "lastname"),
    )
    birthdate_date = fields.Date(
        string="Birthdate",
        help="host birthdate",
        readonly=False,
        store=True,
        compute="_compute_birth_date",
        inverse=lambda r: r._inverse_partner_fields("birthdate_date", "birthdate_date"),
    )
    partner_incongruences = fields.Char(
        help="indicates that some partner fields \
            on the checkin do not correspond to that of \
            the associated partner",
        compute="_compute_partner_incongruences",
    )

    possible_existing_customer_ids = fields.One2many(
        string="Possible existing customer",
        compute="_compute_possible_existing_customer_ids",
        comodel_name="res.partner",
    )

    partner_relationship = fields.Char(help="Family relationship between travelers")

    signature = fields.Image(
        help="Signature of the guest",
    )

    sign_on = fields.Datetime(
        help="Date and time of the signature",
        compute="_compute_sign_on",
    )

    def _inverse_partner_fields(self, checkin_field_name, partner_field_name):
        for record in self:
            if record.partner_id:
                record.partner_id[partner_field_name] = record[checkin_field_name]

    @api.depends("partner_id")
    def _compute_firstname(self):
        for record in self:
            if not record.firstname and record.partner_id.firstname:
                record.firstname = record.partner_id.firstname
            elif not record.firstname:
                record.firstname = False

    @api.depends("partner_id")
    def _compute_lastname(self):
        for record in self:
            if not record.lastname and record.partner_id.lastname:
                record.lastname = record.partner_id.lastname
            elif not record.lastname:
                record.lastname = False

    @api.depends("partner_id")
    def _compute_birth_date(self):
        for record in self:
            if not record.birthdate_date and record.partner_id.birthdate_date:
                record.birthdate_date = record.partner_id.birthdate_date
            elif not record.birthdate_date:
                record.birthdate_date = False

    @api.depends("partner_id")
    def _compute_gender(self):
        for record in self:
            if not record.gender and record.partner_id.gender:
                record.gender = record.partner_id.gender
            elif not record.gender:
                record.gender = False

    @api.depends("partner_id")
    def _compute_nationality_id(self):
        for record in self:
            if not record.nationality_id and record.partner_id.nationality_id:
                record.nationality_id = record.partner_id.nationality_id
            elif not record.nationality_id:
                record.nationality_id = False

    @api.depends("partner_id")
    def _compute_street(self):
        for record in self:
            if not record.street and record.partner_id.street:
                record.street = record.partner_id.street
            elif not record.street:
                record.street = False

    @api.depends("partner_id")
    def _compute_street2(self):
        for record in self:
            if not record.street2 and record.partner_id.street2:
                record.street2 = record.partner_id.street2
            elif not record.street2:
                record.street2 = False

    @api.depends("partner_id")
    def _compute_zip(self):
        for record in self:
            if not record.zip and record.partner_id.zip:
                record.zip = record.partner_id.zip
            elif not record.zip:
                record.zip = False

    @api.depends("partner_id")
    def _compute_city(self):
        for record in self:
            if not record.city and record.partner_id.city:
                record.city = record.partner_id.city
            elif not record.city:
                record.city = False

    @api.depends("partner_id", "nationality_id")
    def _compute_country_id(self):
        for record in self:
            if not record.country_id and record.partner_id.country_id:
                record.country_id = record.partner_id.country_id
            elif not record.state_id:
                record.country_id = False

    @api.depends("partner_id")
    def _compute_state_id(self):
        for record in self:
            if not record.state_id and record.partner_id.state_id:
                record.state_id = record.partner_id.state_id
            elif not record.state_id:
                record.state_id = False

    @api.depends(lambda self: self._checkin_manual_fields())
    def _compute_state(self):
        for record in self:
            if not record.state:
                record.state = "dummy"
            if record.reservation_id.state == "cancel":
                record.state = "cancel"
            elif record.state in ("dummy", "draft", "precheckin", "cancel"):
                if all(
                    not getattr(record, field)
                    for field in record._checkin_manual_fields()
                ):
                    record.state = "dummy"
                elif any(
                    not getattr(record, field)
                    for field in record._checkin_mandatory_fields()
                ):
                    record.state = "draft"
                else:
                    record.state = "precheckin"

    @api.depends("partner_id")
    def _compute_name(self):
        for record in self:
            if not record.name or record.partner_id.name:
                record.name = record.partner_id.name

    @api.depends("partner_id")
    def _compute_email(self):
        for record in self:
            if not record.email and record.partner_id.email:
                record.email = record.partner_id.email
            elif not record.email:
                record.email = False

    @api.depends("partner_id")
    def _compute_mobile(self):
        for record in self:
            if not record.mobile and record.partner_id.mobile:
                record.mobile = record.partner_id.mobile
            elif not record.mobile:
                record.mobile = False

    @api.depends("partner_id")
    def _compute_phone(self):
        for record in self:
            if not record.phone and record.partner_id.phone:
                record.phone = record.partner_id.phone
            elif not record.phone:
                record.phone = False

    def _completed_partner_creation_fields(self):
        self.ensure_one()
        if self.firstname or self.lastname:
            return True
        return False

    def _get_partner_create_vals(self):
        return {
            "firstname": self.firstname,
            "lastname": self.lastname,
            "gender": self.gender,
            "birthdate_date": self.birthdate_date,
            "nationality_id": self.nationality_id.id,
        }

    @api.depends("email", "mobile")
    def _compute_possible_existing_customer_ids(self):
        for record in self:
            possible_customer = self.env[
                "pms.folio"
            ]._apply_possible_existing_customer_ids(record.email, record.mobile)
            if possible_customer:
                record.possible_existing_customer_ids = possible_customer
            else:
                record.possible_existing_customer_ids = False

    @api.model
    def _get_partner_incongruences_field_names(self):
        return [
            "firstname",
            "lastname",
            "gender",
            "birthdate_date",
            "nationality_id",
            "email",
            "mobile",
            "partner_id",
        ]

    @api.depends(lambda self: self._get_partner_incongruences_field_names())
    def _compute_partner_incongruences(self):
        for record in self:
            incongruous_fields = False
            if record.partner_id:
                for field in record._checkin_partner_fields():
                    if (
                        record.partner_id[field]
                        and record.partner_id[field] != record[field]
                    ):
                        if not incongruous_fields:
                            incongruous_fields = record._fields[field].string
                        else:
                            incongruous_fields += ", " + record._fields[field].string
                if incongruous_fields:
                    record.partner_incongruences = (
                        incongruous_fields + " field/s don't correspond to saved host"
                    )
                else:
                    record.partner_incongruences = False
            else:
                record.partner_incongruences = False

    @api.depends("signature")
    def _compute_sign_on(self):
        for record in self:
            if record.signature:
                record.sign_on = datetime.now()
            else:
                record.sign_on = False

    # pylint: disable=W8110
    def _compute_access_url(self):
        super()._compute_access_url()
        for checkin in self:
            checkin.access_url = "/my/folios/{}/reservations/{}/checkins/{}".format(
                checkin.folio_id.id,
                checkin.reservation_id.id,
                checkin.id,
            )

    # Constraints and onchanges

    @api.constrains("departure", "arrival")
    def _check_departure(self):
        for record in self:
            if record.departure and record.arrival > record.departure:
                raise ValidationError(
                    _(
                        "Departure date (%(departure)s) is prior to"
                        " arrival on %(arrival)s",
                        departure=record.departure,
                        arrival=record.arrival,
                    )
                )

    @api.constrains("partner_id")
    def _check_partner_id(self):
        for record in self:
            if record.partner_id:
                indoor_partner_ids = record.reservation_id.checkin_partner_ids.filtered(
                    lambda r, record=record: r.id != record.id
                ).mapped("partner_id.id")
                if indoor_partner_ids.count(record.partner_id.id) > 1:
                    record.partner_id = None
                    raise ValidationError(
                        _("This guest is already registered in the room")
                    )

    def _validation_eval_context(self, id_number):
        self.ensure_one()
        return {"self": self, "id_number": id_number}

    @api.constrains("state_id", "country_id")
    def _check_state_id_country_id_consistence(self):
        for record in self:
            if record.state_id and record.country_id:
                if (
                    record.state_id.country_id
                    and record.country_id not in record.state_id.country_id
                ):
                    raise ValidationError(
                        _("State and country of residence do not match")
                    )

    def set_partner_address(self, residence_vals=None):
        """
        Only sets the checkin.partner address in the associated partner if
        the partner has no address yet or the changes do not conflict with
        the partner's address.
        """
        self.ensure_one()
        if not self.partner_id:
            return
        address_fields = {"street", "street2", "zip", "city", "country_id", "state_id"}
        # If it comes form create, we take the values from the checkin.partner
        if residence_vals is None:
            residence_vals = {
                field: self[field].id if hasattr(self[field], "id") else self[field]
                for field in address_fields
            }

        if any(residence_vals.values()):
            address_fields = residence_vals.keys()
            if any(
                (
                    self.partner_id[field].id
                    if hasattr(self.partner_id[field], "id")
                    else self.partner_id[field]
                )
                != residence_vals.get(field)
                for field in address_fields
                if self.partner_id[field]
            ):
                return
            vals_to_write = {
                field: residence_vals[field]
                for field in address_fields
                if residence_vals.get(field) and not self.partner_id[field]
            }
            if vals_to_write:
                self.partner_id.write(vals_to_write)

    def set_partner_id(self):
        for record in self:
            if not record.partner_id:
                if record._completed_partner_creation_fields():
                    partner_values = record._get_partner_create_vals()
                    partner = self.env["res.partner"].create(partner_values)
                    record.partner_id = partner

    @api.model_create_multi
    def create(self, vals_list):
        records = self.env["pms.checkin.partner"]
        for vals in vals_list:
            # The checkin records are created automatically from adult depends
            # if you try to create one manually, we update one unassigned checkin
            reservation_id = vals.get("reservation_id")
            if reservation_id:
                reservation = self.env["pms.reservation"].browse(reservation_id)
            else:
                raise ValidationError(
                    _("Is mandatory indicate the reservation on the checkin")
                )
            # If a checkin is manually created, we need make sure that
            # the reservation adults are computed
            if not reservation.checkin_partner_ids:
                reservation.flush_recordset()
            dummy_checkins = reservation.checkin_partner_ids.filtered(
                lambda c: c.state == "dummy"
            )
            if len(reservation.checkin_partner_ids) < (
                reservation.adults + reservation.children
            ):
                records += super().create(vals)
            elif len(dummy_checkins) > 0:
                dummy_checkins[0].write(vals)
                records += dummy_checkins[0]
            else:
                raise ValidationError(
                    _(
                        "Is not possible to create the proposed "
                        "check-in in this reservation"
                    )
                )
        records_without_partner = records.filtered(lambda r: not r.partner_id)
        if records_without_partner:
            records_without_partner.set_partner_id()
        for record in records:
            record.set_partner_address()
        return records

    def write(self, vals):
        res = super().write(vals)
        reservations = self.mapped("reservation_id")
        for reservation in reservations:
            tourist_tax_services_cmds = reservation._compute_tourist_tax_lines()
            if tourist_tax_services_cmds:
                reservation.write({"service_ids": tourist_tax_services_cmds})
        if not self._context.get("skip_set_partner_data"):
            records_without_partner = self.filtered(lambda r: not r.partner_id)
            if records_without_partner:
                records_without_partner.with_context(
                    skip_set_partner_data=True
                ).set_partner_id()
            for record in self:
                record.set_partner_address()
        return res

    def unlink(self):
        reservations = self.mapped("reservation_id")
        res = super().unlink()
        reservations._compute_checkin_partner_ids()
        return res

    @api.model
    def _checkin_manual_fields(self, country=False):
        manual_fields = [
            "name",
            "partner_id",
            "email",
            "mobile",
            "phone",
            "gender",
            "firstname",
            "lastname",
            "birthdate_date",
            "nationality_id",
            "street",
            "street2",
            "zip",
            "city",
            "country_id",
            "state_id",
        ]
        return manual_fields

    @api.model
    def _get_depends_state_fields(self):
        manual_fields = self._checkin_manual_fields()
        manual_fields.append("reservation_id.state")
        return manual_fields

    def _checkin_mandatory_fields(self):
        """
        Auxiliar method to return the mandatory fields for checkin.
        It can be extended by modules that need to add more mandatory fields.
        """
        self.ensure_one()
        return []

    @api.model
    def _checkin_partner_fields(self):
        checkin_fields = [
            "firstname",
            "lastname",
            "mobile",
            "email",
            "gender",
            "nationality_id",
            "birthdate_date",
        ]
        return checkin_fields

    @api.model
    def import_room_list_json(self, roomlist_json):
        roomlist_json = json.loads(roomlist_json)
        for checkin_dict in roomlist_json:
            identifier = checkin_dict["identifier"]
            reservation_id = checkin_dict["reservation_id"]
            checkin = (
                self.sudo()
                .env["pms.checkin.partner"]
                .search([("identifier", "=", identifier)])
            )
            reservation = self.env["pms.reservation"].browse(reservation_id)
            if not checkin:
                raise ValidationError(
                    _(
                        "%(identifier)s not found in checkins (%(reservation)s)",
                        identifier=identifier,
                        reservation=reservation.name,
                    )
                )
            checkin_vals = {}
            for key, value in checkin_dict.items():
                if key in ("reservation_id", "folio_id", "identifier"):
                    continue
                checkin_vals[key] = value
            checkin.write(checkin_vals)

    def action_on_board(self):
        for record in self:
            if record.reservation_id.checkin > fields.Date.today():
                raise ValidationError(_("It is not yet checkin day!"))
            if record.reservation_id.checkout < fields.Date.today():
                raise ValidationError(_("Its too late to checkin"))

            if any(
                not getattr(record, field)
                for field in record._checkin_mandatory_fields()
            ):
                raise ValidationError(_("Personal data is missing for check-in"))
            vals = {
                "state": "onboard",
                "arrival": fields.Datetime.now(),
            }
            record.update(vals)
            record.reservation_id.state = "onboard"
            record.identifier = (
                record.reservation_id.pms_property_id.checkin_sequence_id._next_do()
            )

    def action_done(self):
        for record in self.filtered(lambda c: c.state == "onboard"):
            vals = {
                "state": "done",
                "departure": fields.Datetime.now(),
            }
            record.update(vals)
        return True

    def action_undo_onboard(self):
        for record in self.filtered(lambda c: c.state == "onboard"):
            vals = {
                "state": "precheckin",
                "arrival": False,
            }
            record.update(vals)
        return True

    def open_partner(self):
        """Utility method used to add an "View Customer" button
        in checkin partner views"""
        self.ensure_one()
        partner_form_id = self.env.ref("pms.view_partner_data_form").id
        return {
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "form",
            "views": [(partner_form_id, "form")],
            "res_id": self.partner_id.id,
            "target": "new",
            "flags": {"form": {"action_buttons": True}},
        }

    def open_wizard_several_partners(self):
        ctx = dict(
            checkin_partner_id=self.id,
            possible_existing_customer_ids=self.possible_existing_customer_ids.ids,
        )
        return {
            "view_type": "form",
            "view_mode": "form",
            "name": "Several Customers",
            "res_model": "pms.several.partners.wizard",
            "target": "new",
            "type": "ir.actions.act_window",
            "context": ctx,
        }

    def send_portal_invitation_email(self, invitation_firstname=None, email=None):
        template = self.sudo().env.ref(
            "pms.precheckin_invitation_email", raise_if_not_found=False
        )
        subject = template._render_field(
            "subject", [6, 0, self.id], compute_lang=True, post_process=True
        )[self.id]
        body = template._render_field(
            "body_html", [6, 0, self.id], compute_lang=True, post_process=True
        )[self.id]
        invitation_mail = (
            self.env["mail.mail"]
            .sudo()
            .create(
                {
                    "subject": subject,
                    "body_html": body,
                    "email_from": self.pms_property_id.partner_id.email,
                    "email_to": email,
                }
            )
        )

        invitation_mail.send()

    def send_exit_email(self, template_id):
        template = self.env["mail.template"].browse(template_id)
        if self.email:
            template.send_mail(
                self.id,
                force_send=True,
                raise_exception=False,
                email_values={"email_to": self.email, "auto_delete": False},
            )
            body = template._render_field(
                "body_html", [6, 0, self.id], compute_lang=True, post_process=True
            )[self.id]
            self.reservation_id.message_post(body=body)

        if self.reservation_id.to_send_exit_mail:
            emails = self.reservation_id.checkin_partner_ids.mapped("email")
            if (
                self.reservation_id.partner_id
                and self.reservation_id.partner_id.email
                and self.reservation_id.partner_id.email not in emails
            ):
                template.send_mail(
                    self.partner_id.id,
                    force_send=True,
                    raise_exception=False,
                    email_values={
                        "email_to": self.reservation_id.email,
                        "auto_delete": False,
                    },
                )
                body = template._render_field(
                    "body_html", [6, 0, self.id], compute_lang=True, post_process=True
                )[self.id]
                self.reservation_id.message_post(body=body)
            self.reservation_id.to_send_exit_mail = False
