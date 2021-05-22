# Copyright 2017  Dario Lodeiros
# Copyright 2018  Alexandre Diaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsCheckinPartner(models.Model):
    _name = "pms.checkin.partner"
    _description = "Partner Checkins"
    _rec_name = "identifier"
    _check_pms_properties_auto = True

    identifier = fields.Char(
        string="Identifier",
        help="Checkin Partner Id",
        readonly=True,
        index=True,
        default=lambda self: _("New"),
    )
    partner_id = fields.Many2one(
        string="Partner",
        help="Partner associated with checkin partner",
        comodel_name="res.partner",
        domain="[('is_company', '=', False)]",
    )
    reservation_id = fields.Many2one(
        string="Reservation",
        help="Reservation to which checkin partners belong",
        comodel_name="pms.reservation",
        check_pms_properties=True,
    )
    folio_id = fields.Many2one(
        string="Folio",
        help="Folio to which reservation of checkin partner belongs",
        store=True,
        comodel_name="pms.folio",
        compute="_compute_folio_id",
        check_pms_properties=True,
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Property to which the folio associated belongs",
        readonly=True,
        store=True,
        comodel_name="pms.property",
        related="folio_id.pms_property_id",
        check_pms_properties=True,
    )
    name = fields.Char(
        string="Name",
        help="Checkin partner name",
        readonly=False,
        store=True,
        compute="_compute_name",
    )
    email = fields.Char(
        string="E-mail",
        help="Checkin Partner Email",
        readonly=False,
        store=True,
        compute="_compute_email",
    )
    mobile = fields.Char(
        string="Mobile",
        help="Checkin Partner Mobile",
        compute="_compute_mobile",
        store=True,
        readonly=False,
    )
    image_128 = fields.Image(
        string="Image",
        help="Checkin Partner Image, it corresponds with Partner Image associated",
        related="partner_id.image_128",
    )
    segmentation_ids = fields.Many2many(
        string="Segmentation",
        help="Segmentation tags to classify checkin partners",
        related="reservation_id.segmentation_ids",
        readonly=True,
    )
    checkin = fields.Date(
        string="Checkin",
        help="Checkin date",
        store=True,
        related="reservation_id.checkin",
        depends=["reservation_id.checkin"],
    )
    checkout = fields.Date(
        string="Checkout",
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
        string="State",
        help="Status of the checkin partner regarding the reservation",
        readonly=True,
        store=True,
        selection=[
            ("draft", "Unkown Guest"),
            ("precheckin", "Pending arrival"),
            ("onboard", "On Board"),
            ("done", "Out"),
            ("cancelled", "Cancelled"),
        ],
        compute="_compute_state",
    )

    # Compute
    @api.depends("reservation_id", "folio_id", "reservation_id.preferred_room_id")
    def _compute_identifier(self):
        for record in self:
            # TODO: Identifier
            checkins = []
            if record.reservation_id.filtered("preferred_room_id"):
                checkins = record.reservation_id.checkin_partner_ids
                record.identifier = (
                    record.reservation_id.preferred_room_id.name
                    + "-"
                    + str(len(checkins) - 1)
                )
            elif record.folio_id:
                record.identifier = record.folio_id.name + "-" + str(len(checkins) - 1)
            else:
                record.identifier = False

    @api.depends("reservation_id", "reservation_id.folio_id")
    def _compute_folio_id(self):
        for record in self.filtered("reservation_id"):
            record.folio_id = record.reservation_id.folio_id

    @api.depends(lambda self: self._checkin_mandatory_fields(depends=True))
    def _compute_state(self):
        for record in self:
            if not record.state:
                record.state = "draft"
            if record.reservation_id.state == "cancelled":
                record.state = "cancelled"
            elif record.state in ("draft", "cancelled"):
                if any(
                    not getattr(record, field)
                    for field in record._checkin_mandatory_fields()
                ):
                    record.state = "draft"
                else:
                    record.state = "precheckin"

    @api.depends(
        "partner_id",
        "partner_id.name",
        "reservation_id",
        "reservation_id.preferred_room_id",
    )
    def _compute_name(self):
        for record in self:
            if not record.name:
                record.name = record.partner_id.name

    @api.depends("partner_id", "partner_id.email")
    def _compute_email(self):
        for record in self:
            if not record.email:
                record.email = record.partner_id.email

    @api.depends("partner_id", "partner_id.mobile")
    def _compute_mobile(self):
        for record in self:
            if not record.mobile:
                record.mobile = record.partner_id.mobile

    @api.constrains("departure", "arrival")
    def _check_departure(self):
        for record in self:
            if record.departure and record.arrival > record.departure:
                raise ValidationError(
                    _("Departure date (%s) is prior to arrival on %s")
                    % (record.departure, record.arrival)
                )

    @api.constrains("partner_id")
    def _check_partner_id(self):
        for record in self:
            if record.partner_id:
                indoor_partner_ids = record.reservation_id.checkin_partner_ids.filtered(
                    lambda r: r.id != record.id
                ).mapped("partner_id.id")
                if indoor_partner_ids.count(record.partner_id.id) > 1:
                    record.partner_id = None
                    raise ValidationError(
                        _("This guest is already registered in the room")
                    )

    @api.constrains("email")
    def check_email_pattern(self):
        for record in self:
            if record.email:
                if not re.search(
                    r"^[a-zA-Z0-9]([a-zA-z0-9\-\_]*[\.]?[a-zA-Z0-9\-\_]+)*"
                    r"@([a-zA-z0-9\-]+([\.][a-zA-Z0-9\-\_]+)?\.[a-zA-Z0-9]+)+$",
                    record.email,
                ):
                    raise ValidationError(_("'%s' is not a valid email", record.email))

    @api.constrains("mobile")
    def check_phone_pattern(self):

        for record in self:
            if record.mobile:

                if not re.search(
                    r"^(\d{3}[\-\s]?\d{2}[\-\s]?\d{2}[\-\s]?\d{2}[\-\s]?|"
                    r"\d{3}[\-\s]?\d{3}[\-\s]?\d{3})$",
                    str(record.mobile),
                ):
                    raise ValidationError(_("'%s' is not a valid phone", record.mobile))

    @api.model
    def create(self, vals):
        # The checkin records are created automatically from adult depends
        # if you try to create one manually, we update one unassigned checkin
        reservation_id = vals.get("reservation_id")
        if reservation_id:
            reservation = self.env["pms.reservation"].browse(reservation_id)
        else:
            raise ValidationError(
                _("Is mandatory indicate the reservation on the checkin")
            )
        draft_checkins = reservation.checkin_partner_ids.filtered(
            lambda c: c.state == "draft"
        )
        if len(reservation.checkin_partner_ids) < reservation.adults:
            if vals.get("identifier", _("New")) == _("New") or "identifier" not in vals:
                pms_property_id = (
                    self.env.user.get_active_property_ids()[0]
                    if "pms_property_id" not in vals
                    else vals["pms_property_id"]
                )
                pms_property = self.env["pms.property"].browse(pms_property_id)
                vals["identifier"] = pms_property.folio_sequence_id._next_do()
            return super(PmsCheckinPartner, self).create(vals)
        if len(draft_checkins) > 0:
            draft_checkins[0].write(vals)
            return draft_checkins[0]
        raise ValidationError(
            _("Is not possible to create the proposed check-in in this reservation")
        )

    def write(self, vals):
        res = super(PmsCheckinPartner, self).write(vals)
        ResPartner = self.env["res.partner"]
        if any(field in vals for field in ResPartner._get_key_fields()):
            # Create Partner if get key field in the checkin
            for record in self:
                key = False
                partner = False
                if not record.partner_id:
                    partner_vals = {}
                    for field in self._checkin_partner_fields():
                        if getattr(record, field):
                            partner_vals[field] = getattr(record, field)
                        if field in ResPartner._get_key_fields() and partner_vals.get(
                            field
                        ):
                            key = True
                            # REVIEW: if partner exist, we can merge?
                            partner = ResPartner.search(
                                [(field, "=", getattr(record, field))]
                            )
                    if key:
                        if not partner:
                            partner = ResPartner.create(partner_vals)
                        record.partner_id = partner

        if any(field in vals for field in self._checkin_partner_fields()):
            # Update partner when the checkin partner field is not set on the partner
            for record in self:
                if record.partner_id:
                    partner_vals = {}
                    for field in self._checkin_partner_fields():
                        if not getattr(record.partner_id, field):
                            partner_vals[field] = getattr(record, field)
                    record.partner_id.write(partner_vals)
        return res

    def unlink(self):
        reservations = self.mapped("reservation_id")
        res = super().unlink()
        reservations._compute_checkin_partner_ids()
        return res

    @api.model
    def _checkin_mandatory_fields(self, depends=False):
        # api.depends need "reservation_id.state" in the lambda function
        if depends:
            return ["reservation_id.state", "name"]
        return ["name"]

    @api.model
    def _checkin_partner_fields(self):
        # api.depends need "reservation_id.state" in the lambda function
        checkin_fields = self._checkin_mandatory_fields()
        checkin_fields.extend(["mobile", "email"])
        return checkin_fields

    @api.model
    def import_room_list_json(self, roomlist_json):
        roomlist_json = json.loads(roomlist_json)
        for checkin_dict in roomlist_json:
            identifier = checkin_dict["identifier"]
            reservation_id = checkin_dict["reservation_id"]
            checkin = self.env["pms.checkin.partner"].search(
                [("identifier", "=", identifier)]
            )
            reservation = self.env["pms.reservation"].browse(reservation_id)
            if not checkin:
                raise ValidationError(
                    _("%s not found in checkins (%s)"), identifier, reservation.name
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
            if record.reservation_id.checkout <= fields.Date.today():
                raise ValidationError(_("Its too late to checkin"))
            if any(
                not getattr(record, field) for field in self._checkin_mandatory_fields()
            ):
                raise ValidationError(_("Personal data is missing for check-in"))
            vals = {
                "state": "onboard",
                "arrival": fields.Datetime.now(),
            }
            record.update(vals)
            if record.reservation_id.allowed_checkin:
                record.reservation_id.state = "onboard"

    def action_done(self):
        for record in self.filtered(lambda c: c.state == "onboard"):
            vals = {
                "state": "done",
                "departure": fields.Datetime.now(),
            }
            record.update(vals)
        return True
