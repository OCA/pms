# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import datetime
import re

import pytz

from odoo import _, api, fields, models, modules
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

from odoo.addons.base.models.res_partner import _tz_get

HOUR_STR_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def get_default_logo():
    with open(
        modules.get_module_resource("pms", "static/img", "property_logo.png"), "rb"
    ) as f:
        return base64.b64encode(f.read())


class PmsProperty(models.Model):
    _name = "pms.property"
    _description = "Property"
    _inherits = {"res.partner": "partner_id"}
    _inherit = ["mail.thread"]
    _check_company_auto = True

    partner_id = fields.Many2one(
        string="Property",
        help="Current property",
        comodel_name="res.partner",
        required=True,
        index=True,
        ondelete="restrict",
    )
    parent_id = fields.Many2one(
        comodel_name="pms.property", string="Parent Property", index=True
    )
    child_ids = fields.One2many(
        comodel_name="pms.property", inverse_name="parent_id", string="Child Properties"
    )
    pms_property_code = fields.Char(
        string="Property Code",
        help="Short name property",
    )
    company_id = fields.Many2one(
        string="Company",
        help="The company that owns or operates this property.",
        comodel_name="res.company",
        index=True,
        required=True,
    )
    user_ids = fields.Many2many(
        string="Accepted Users",
        help="Field related to res.users. Allowed users on the property",
        comodel_name="res.users",
        relation="pms_property_users_rel",
        column1="pms_property_id",
        column2="user_id",
    )
    room_ids = fields.One2many(
        string="Rooms",
        help="Rooms that a property has.",
        comodel_name="pms.room",
        inverse_name="pms_property_id",
    )
    default_pricelist_id = fields.Many2one(
        string="Product Pricelist",
        help="The default pricelist used in this property.",
        comodel_name="product.pricelist",
        required=True,
        index=True,
        domain="[('is_pms_available', '=', True)]",
        default=lambda self: self.env.ref("product.list0").id,
    )
    default_arrival_hour = fields.Char(
        string="Arrival Hour", help="HH:mm Format", default="14:00", required=True
    )
    default_departure_hour = fields.Char(
        string="Departure Hour", help="HH:mm Format", default="12:00", required=True
    )
    folio_sequence_id = fields.Many2one(
        string="Folio Sequence",
        help="The sequence that formed the name of the folio.",
        check_company=True,
        copy=False,
        index=True,
        comodel_name="ir.sequence",
    )
    checkin_sequence_id = fields.Many2one(
        string="Checkin Sequence",
        help="Field used to create the name of the checkin partner",
        check_company=True,
        copy=False,
        index=True,
        comodel_name="ir.sequence",
    )
    tz = fields.Selection(
        string="Timezone",
        help="This field is used to determine de timezone of the property.",
        required=True,
        default=lambda self: self.env.user.tz or "UTC",
        selection=_tz_get,
    )
    cardex_warning = fields.Text(
        string="Warning in Cardex",
        default="Time to access rooms: 14: 00h. "
        "Departure time: 12: 00h. If the accommodation "
        "is not left at that time, the establishment will "
        "charge a day's stay according to current rate that day",
        help="Notice under the signature on the traveler's ticket.",
    )
    free_room_ids = fields.One2many(
        string="Rooms available",
        help="allows you to send different parameters in the context "
        "(checkin(required), checkout(required), room_type_id, ubication_id, capacity, "
        "amenity_ids and / or pricelist_id) and return rooms available",
        comodel_name="pms.room",
        compute="_compute_free_room_ids",
    )
    availability = fields.Integer(
        string="Number of rooms available",
        help="allows you to send different parameters in the context "
        "(checkin(required), checkout(required), room_type_id, ubication_id, capacity,"
        "amenity_ids and / or pricelist_id) check the availability for the hotel",
        compute="_compute_availability",
    )
    mail_information = fields.Html(help="Additional information of the mail")
    privacy_policy = fields.Html(help="Mail privacy policy ")
    property_confirmed_template = fields.Many2one(
        string="Confirmation Email",
        help="Confirmation email template",
        comodel_name="mail.template",
    )
    property_modified_template = fields.Many2one(
        string="Modification Email",
        help="Modification email template",
        comodel_name="mail.template",
    )
    property_exit_template = fields.Many2one(
        string="Exit Email",
        comodel_name="mail.template",
    )
    property_canceled_template = fields.Many2one(
        string="Cancellation Email",
        help="Cancellation email template",
        comodel_name="mail.template",
    )
    is_confirmed_auto_mail = fields.Boolean(string="Auto Send Confirmation Mail")
    is_modified_auto_mail = fields.Boolean(string="Auto Send Modification Mail")
    is_exit_auto_mail = fields.Boolean(string="Auto Send Exit Mail")
    is_canceled_auto_mail = fields.Boolean(string="Auto Send Cancellation Mail")

    journal_simplified_invoice_id = fields.Many2one(
        string="Simplified Invoice Journal",
        comodel_name="account.journal",
        domain=[
            ("type", "=", "sale"),
        ],
        help="Journal used to create the simplified invoice",
        check_company=True,
        check_pms_properties=True,
    )
    journal_normal_invoice_id = fields.Many2one(
        string="Normal Invoice Journal",
        comodel_name="account.journal",
        domain=[
            ("type", "=", "sale"),
            ("is_simplified_invoice", "=", False),
        ],
        help="Journal used to create the normal invoice",
        check_company=True,
        check_pms_properties=True,
    )
    max_amount_simplified_invoice = fields.Float(
        help="Maximum amount to create the simplified invoice",
        default=400.0,
    )
    avoid_simplified_max_amount_downpayment = fields.Boolean(
        string="Downpayment Invoive without limit amount",
        help="Avoid simplified invoice max amount downpayment",
        default=True,
    )
    user_id = fields.Many2one(
        string="Team Leader",
        copy=False,
        comodel_name="res.users",
        ondelete="restrict",
        tracking=True,
    )
    member_ids = fields.One2many(
        string="Team Members",
        comodel_name="pms.team.member",
        inverse_name="pms_property_id",
        copy=False,
    )
    logo = fields.Binary(
        string="Image in checkin",
        default=get_default_logo(),
    )
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        readonly=True,
        copy=False,
    )
    block_create_past_reservations = fields.Boolean(
        help="Block the creation of reservations in the past",
        default=False,
    )
    block_modify_past_out_service = fields.Boolean(
        help="Block deletion or cancellation of out-of-service reservations "
        "with dates already in the past",
        default=False,
    )
    invoice_reservation_note_template = fields.Text(
        translate=True,
        help="""
            Template for reservation note to be added in the invoice.
            You can use variables like {{ object.checkin }}, etc.
        """,
    )

    @api.depends_context(
        "checkin",
        "checkout",
        "real_avail",
        "room_type_id",
        "ubication_id",
        "capacity",
        "amenity_ids",
        "pricelist_id",
        "class_id",
        "overnight_rooms",
        "current_lines",
    )
    def _compute_free_room_ids(self):
        checkin = self._context["checkin"]
        checkout = self._context["checkout"]

        if isinstance(checkin, str):
            checkin = datetime.datetime.strptime(
                checkin, DEFAULT_SERVER_DATE_FORMAT
            ).date()
        if isinstance(checkout, str):
            checkout = datetime.datetime.strptime(
                checkout, DEFAULT_SERVER_DATE_FORMAT
            ).date()
        current_lines = self.env.context.get("current_lines", False)
        if current_lines and not isinstance(current_lines, list):
            current_lines = [current_lines]
        pricelist_id = self.env.context.get("pricelist_id", False)
        room_type_id = self.env.context.get("room_type_id", False)
        class_id = self._context.get("class_id", False)
        real_avail = self._context.get("real_avail", False)
        overnight_rooms = self._context.get("overnight_rooms", False)
        capacity = self._context.get("capacity", False)
        for pms_property in self:
            free_rooms = pms_property.get_real_free_rooms(
                checkin, checkout, current_lines
            )
            if pricelist_id and not real_avail:
                # TODO: only closed_departure take account checkout date!
                domain_rules = [
                    ("date", ">=", checkin),
                    ("date", "<=", checkout),
                    ("pms_property_id", "=", pms_property.id),
                ]
                if room_type_id:
                    domain_rules.append(("room_type_id", "=", room_type_id))

                pricelist = self.env["product.pricelist"].browse(pricelist_id)
                if pricelist.availability_plan_id:
                    domain_rules.append(
                        ("availability_plan_id", "=", pricelist.availability_plan_id.id)
                    )
                    rule_items = self.env["pms.availability.plan.rule"].search(
                        domain_rules
                    )

                    if len(rule_items) > 0:
                        room_types_to_remove = []
                        for item in rule_items:
                            if pricelist.availability_plan_id.any_rule_applies(
                                checkin, checkout, item
                            ):
                                room_types_to_remove.append(item.room_type_id.id)
                        free_rooms = free_rooms.filtered(
                            lambda x, rttr=room_types_to_remove: x.room_type_id.id
                            not in rttr
                        )
            if class_id:
                free_rooms = free_rooms.filtered(
                    lambda x: x.room_type_id.class_id.id == class_id
                )
            if overnight_rooms:
                free_rooms = free_rooms.filtered(
                    lambda x: x.room_type_id.overnight_room
                )
            if capacity:
                free_rooms = free_rooms.filtered(lambda x: x.capacity >= capacity)
            if len(free_rooms) > 0:
                pms_property.free_room_ids = free_rooms.ids
            else:
                pms_property.free_room_ids = False

    def get_real_free_rooms(self, checkin, checkout, current_lines=False):
        self.ensure_one()
        Avail = self.env["pms.availability"]
        target_rooms = (
            self.env["pms.room"]
            .with_context(active_test=True)
            .search([("pms_property_id", "=", self.id)])
        )

        room_type_id = self.env.context.get("room_type_id", False)
        if room_type_id:
            target_rooms = target_rooms.filtered(
                lambda r: r.room_type_id.id == room_type_id
            )
        capacity = self.env.context.get("capacity", False)
        if capacity:
            target_rooms = target_rooms.filtered(lambda r: r.capacity >= capacity)

        ubication_id = self.env.context.get("ubication_id", False)
        if ubication_id:
            target_rooms = target_rooms.filtered(
                lambda r: r.ubication_id.id == ubication_id
            )

        amenity_ids = self.env.context.get("amenity_ids", False)
        if amenity_ids:
            if amenity_ids and not isinstance(amenity_ids, list):
                amenity_ids = [amenity_ids]
            target_rooms = target_rooms.filtered(
                lambda r: len(set(amenity_ids) - set(r.room_amenity_ids.ids)) == 0
            )

        if not current_lines:
            current_lines = []

        rooms_not_avail_ids = Avail.get_rooms_not_avail(
            checkin=checkin,
            checkout=checkout,
            room_ids=target_rooms.ids,
            pms_property_id=self.id,
            current_lines=current_lines,
        )
        domain_rooms = [("id", "in", target_rooms.ids)]
        if rooms_not_avail_ids:
            domain_rooms.append(
                ("id", "not in", rooms_not_avail_ids),
            )
        return self.env["pms.room"].with_context(active_test=True).search(domain_rooms)

    @api.depends_context(
        "checkin",
        "checkout",
        "real_avail",
        "room_type_id",
        "ubication_id",
        "capacity",
        "amenity_ids",
        "pricelist_id",
        "class_id",
        "overnight_rooms",
        "current_lines",
    )
    def _compute_availability(self):
        for record in self:
            checkin = self._context["checkin"]
            checkout = self._context["checkout"]
            if isinstance(checkin, str):
                checkin = datetime.datetime.strptime(
                    checkin, DEFAULT_SERVER_DATE_FORMAT
                ).date()
            if isinstance(checkout, str):
                checkout = datetime.datetime.strptime(
                    checkout, DEFAULT_SERVER_DATE_FORMAT
                ).date()
            room_type_id = self.env.context.get("room_type_id", False)
            pricelist_id = self.env.context.get("pricelist_id", False)
            current_lines = self.env.context.get("current_lines", [])
            class_id = self._context.get("class_id", False)
            real_avail = self._context.get("real_avail", False)
            overnight_rooms = self._context.get("overnight_rooms", False)
            capacity = self._context.get("capacity", False)
            pms_property = record.with_context(
                checkin=checkin,
                checkout=checkout,
                room_type_id=room_type_id,
                current_lines=current_lines,
                pricelist_id=pricelist_id,
                class_id=class_id,
                real_avail=real_avail,
                overnight_rooms=overnight_rooms,
                capacity=capacity,
            )
            count_avail_rooms = len(pms_property.free_room_ids)
            if current_lines and not isinstance(current_lines, list):
                current_lines = [current_lines]

            domain_rules = [
                ("date", ">=", checkin),
                ("date", "<=", checkout),
                ("pms_property_id", "=", pms_property.id),
            ]
            if room_type_id:
                domain_rules.append(("room_type_id", "=", room_type_id))

            room_types = (
                [self.env["pms.room.type"].browse(room_type_id)]
                if room_type_id
                else record.room_ids.mapped("room_type_id")
            )

            pricelist = False
            if pricelist_id:
                pricelist = self.env["product.pricelist"].browse(pricelist_id)
            if pricelist and pricelist.availability_plan_id and not real_avail:
                # The availability between two dates is given in two steps:
                # 1- the date with minimum availability is obtained for each room_type
                # 2- the availabilities of the room_type with dispo > 0 are added
                days = [
                    checkin + datetime.timedelta(days=i)
                    for i in range((checkout - checkin).days + 1)
                ]
                day_avail = {}
                domain_rules.append(
                    ("availability_plan_id", "=", pricelist.availability_plan_id.id)
                )
                rule_groups = (
                    self.env["pms.availability.plan.rule"]
                    .sudo()
                    .with_context(lang="en_US")
                    .read_group(
                        domain_rules,
                        ["plan_avail:sum"],
                        ["date:day"],
                        lazy=False,
                    )
                )
                grouped_rules = {}
                for group in rule_groups:
                    # Use ISO ``__range`` boundary: the ``date:day`` label is
                    # locale-formatted and ``with_context(lang="en_US")`` is
                    # ignored when ``en_US`` is not installed.
                    date = fields.Date.from_string(group["__range"]["date:day"]["from"])
                    for rt in room_types:
                        group_avail = group["plan_avail"]
                        items = self.env["pms.availability.plan.rule"].search(
                            group["__domain"]
                        )
                        for item in items:
                            if pricelist.availability_plan_id.any_rule_applies(
                                checkin, checkout, item
                            ):
                                group_avail -= item.plan_avail
                        grouped_rules[(date, rt.id)] = (
                            grouped_rules.get((date, rt.id), 0) + group_avail
                        )
                # Avoid take account availability for checkout date
                for day in days[:-1]:
                    total_avail_day = 0
                    for rt in room_types:
                        key = (day, rt.id)
                        if key in grouped_rules:
                            total_avail_day += grouped_rules[key]
                        else:
                            # If not rule found for the any date/room_type
                            # we need take account the default availability
                            # of the room type
                            # ATENTION: default avail not apply for checkout date
                            default_avail = min(
                                filter(
                                    lambda x: x != -1,
                                    [
                                        rt.default_quota,
                                        rt.default_max_avail,
                                        len(
                                            record.with_context(
                                                checkin=day,
                                                checkout=day + datetime.timedelta(1),
                                                room_type_id=rt.id,
                                                current_lines=current_lines,
                                                pricelist_id=pricelist.id,
                                                real_avail=True,
                                            ).free_room_ids
                                        ),
                                    ],
                                )
                            )
                            total_avail_day += default_avail
                    day_avail[day] = total_avail_day
                if day_avail:
                    count_avail_rooms = min(day_avail.values())
            record.availability = count_avail_rooms

    @api.model
    def splitted_availability(
        self,
        checkin,
        checkout,
        pms_property_id,
        room_type_id=False,
        current_lines=False,
        pricelist=False,
        real_avail=False,
    ):
        if isinstance(checkin, str):
            checkin = datetime.datetime.strptime(
                checkin, DEFAULT_SERVER_DATE_FORMAT
            ).date()
        if isinstance(checkout, str):
            checkout = datetime.datetime.strptime(
                checkout, DEFAULT_SERVER_DATE_FORMAT
            ).date()
        for date_iterator in [
            checkin + datetime.timedelta(days=x)
            for x in range(0, (checkout - checkin).days)
        ]:
            pms_property = self.env["pms.property"].browse(pms_property_id)
            pms_property = pms_property.with_context(
                checkin=date_iterator,
                checkout=date_iterator + datetime.timedelta(1),
                room_type_id=room_type_id,
                current_lines=current_lines,
                pricelist_id=pricelist.id,
                real_avail=real_avail,
            )

            if len(pms_property.free_room_ids) < 1:
                return False
        return True

    @api.constrains("ref")
    def _check_unique_property_ref(self):
        for record in self:
            if record.ref:
                duplicated = self.env["pms.property"].search(
                    [("ref", "=", record.ref), ("id", "!=", record.id)]
                )
                if duplicated:
                    raise ValidationError(
                        _(
                            "Alreay exist other property "
                            "with this ref: %(name)s (%(ref)s)",
                            name=duplicated.name,
                            ref=duplicated.ref,
                        )
                    )

    @api.constrains("pms_property_code")
    def _check_unique_property_code(self):
        for record in self:
            if record.pms_property_code:
                duplicated = self.env["pms.property"].search(
                    [
                        ("pms_property_code", "=", record.pms_property_code),
                        ("id", "!=", record.id),
                    ]
                )
                if duplicated:
                    raise ValidationError(
                        _(
                            "Alreay exist other property "
                            "with this code: %(name)s (%(code)s)",
                            name=duplicated.name,
                            code=duplicated.pms_property_code,
                        )
                    )

    @api.constrains("default_arrival_hour")
    def _check_arrival_hour(self):
        for record in self:
            if not self.is_valid_hour_str(record.default_arrival_hour):
                raise ValidationError(
                    _("Format Arrival Hour (HH:MM) Error: %s")
                    % record.default_arrival_hour
                )

    @api.constrains("default_departure_hour")
    def _check_departure_hour(self):
        for record in self:
            if not self.is_valid_hour_str(record.default_departure_hour):
                raise ValidationError(
                    _("Format Departure Hour (HH:MM) Error: %s")
                    % record.default_departure_hour
                )

    @api.model
    def is_valid_hour_str(self, hour_str):
        """Return whether hour_str is a zero-padded 24h "HH:MM" string.

        Stricter on purpose than time.strptime(hour_str, "%H:%M"), which
        also accepts hours without zero padding ("8:00") that the hour
        consumers, parsing by position, cannot read back.
        """
        return bool(hour_str) and bool(HOUR_STR_PATTERN.match(hour_str))

    @api.model
    def hour_str_to_time(self, hour_str):
        """Return the "HH:MM" hour_str as a datetime.time."""
        if not self.is_valid_hour_str(hour_str):
            raise ValidationError(_("Format Hour (HH:MM) Error: %s") % hour_str)
        hour, minute = hour_str.split(":")
        return datetime.time(int(hour), int(minute))

    def datetime_from_hour_str(self, local_date, hour_str):
        """Return local_date at hour_str, from property to user timezone."""
        self.ensure_one()
        local_dt = datetime.datetime.combine(
            local_date, self.hour_str_to_time(hour_str)
        )
        return self.date_property_timezone(local_dt)

    def date_property_timezone(self, dt):
        self.ensure_one()
        if self.env.user:
            tz_property = self.tz
            dt = pytz.timezone(tz_property).localize(dt)
            dt = dt.replace(tzinfo=None)
            dt = pytz.timezone(self.env.user.tz or "UTC").localize(dt)
            dt = dt.astimezone(pytz.utc)
            dt = dt.replace(tzinfo=None)
        return dt

    def _get_payment_methods(self, automatic_included=False, room_ids=False):
        # We use automatic_included to True to see absolutely
        # all the journals with associated payments, if it is
        # false, we will only see those journals that can be used
        # to pay manually
        # room_ids [list] is used to filter the payment methods
        # by rooms (usefull in apartments, villas, etc)
        self.ensure_one()
        journals = self.env["account.journal"].search(
            [
                ("type", "in", ["cash", "bank"]),
                "|",
                ("pms_property_ids", "in", self.id),
                "|",
                "&",
                ("pms_property_ids", "=", False),
                ("company_id", "=", self.company_id.id),
                "&",
                ("pms_property_ids", "=", False),
                ("company_id", "=", False),
            ]
        )
        if room_ids:
            journals = journals.filtered(
                lambda p: not p.room_filter_ids
                or any(room_id in p.room_filter_ids.ids for room_id in room_ids)
            )
        method_lines = journals.mapped("inbound_payment_method_line_ids")
        if not automatic_included:
            method_lines = method_lines.filtered(lambda ml: ml.allowed_on_pms)
        return method_lines

    @api.model_create_multi
    def create(self, vals_list):
        records = self.env["pms.property"]
        for vals in vals_list:
            name = vals.get("name")
            if "folio_sequence_id" not in vals or not vals.get("folio_sequence_id"):
                folio_sequence = self.env["ir.sequence"].create(
                    {
                        "name": "PMS Folio " + name,
                        "code": "pms.folio",
                        "prefix": "F/%(y)s",
                        "suffix": "%(sec)s",
                        "padding": 4,
                        "company_id": vals.get("company_id"),
                    }
                )
                vals.update({"folio_sequence_id": folio_sequence.id})
            if "checkin_sequence_id" not in vals or not vals.get("checkin_sequence_id"):
                checkin_sequence = self.env["ir.sequence"].create(
                    {
                        "name": "PMS Checkin " + name,
                        "code": "pms.checkin.partner",
                        "prefix": "C/%(y)s",
                        "suffix": "%(sec)s",
                        "padding": 4,
                        "company_id": vals.get("company_id"),
                    }
                )
                vals.update({"checkin_sequence_id": checkin_sequence.id})
            # create analytic account
            analytic_account = self.env["account.analytic.account"].create(
                {
                    "name": name,
                    "code": vals.get("pms_property_code"),
                    "plan_id": self.env.ref("pms.main_pms_analytic_plan").id,
                    "company_id": vals.get("company_id"),
                }
            )
            vals.update({"analytic_account_id": analytic_account.id})
            record = super(
                PmsProperty, self.with_context(avoid_document_restriction=True)
            ).create(vals)
            records += record
            # analityc distribution by default
            self.env["account.analytic.distribution.model"].create(
                {
                    "pms_property_id": record.id,
                    "analytic_distribution": {analytic_account.id: 100},
                    "company_id": record.company_id.id,
                }
            )
        return records

    @api.model
    def daily_closing(
        self, pms_property_ids, room_type_ids=False, availability_plan_ids=False
    ):
        """
        This method is used to close the daily availability of rooms
        """
        pms_properties = self.browse(pms_property_ids)
        for pms_property in pms_properties:
            if not room_type_ids:
                room_type_ids = (
                    self.env["pms.room.type"]
                    .search(
                        [
                            "|",
                            ("pms_property_ids", "in", pms_property.id),
                            ("pms_property_ids", "=", False),
                        ]
                    )
                    .ids
                )
            if not availability_plan_ids:
                availability_plan_ids = (
                    self.env["pms.availability.plan"]
                    .search(
                        [
                            "|",
                            ("pms_property_ids", "in", pms_property.id),
                            ("pms_property_ids", "=", False),
                        ]
                    )
                    .ids
                )
            for room_type in self.env["pms.room.type"].browse(room_type_ids):
                for availability_plan in self.env["pms.availability.plan"].browse(
                    availability_plan_ids
                ):
                    rule = self.env["pms.availability.plan.rule"].search(
                        [
                            ("pms_property_id", "=", pms_property.id),
                            ("room_type_id", "=", room_type.id),
                            ("availability_plan_id", "=", availability_plan.id),
                            ("date", "=", fields.date.today()),
                        ]
                    )
                    if not rule:
                        rule = self.env["pms.availability.plan.rule"].create(
                            {
                                "pms_property_id": pms_property.id,
                                "room_type_id": room_type.id,
                                "availability_plan_id": availability_plan.id,
                                "date": fields.date.today(),
                                "closed": True,
                            }
                        )
                    elif not rule.closed:
                        rule.write(
                            {
                                "closed": True,
                            }
                        )
        return True

    @api.constrains("journal_normal_invoice_id")
    def _check_journal_normal_invoice(self):
        for pms_property in self.filtered("journal_normal_invoice_id"):
            if pms_property.journal_normal_invoice_id.is_simplified_invoice:
                raise ValidationError(
                    _("Journal %s is not allowed to be used for normal invoices")
                    % pms_property.journal_normal_invoice_id.name
                )

    @api.constrains("journal_simplified_invoice_id")
    def _check_journal_simplified_invoice(self):
        for pms_property in self.filtered("journal_simplified_invoice_id"):
            if not pms_property.journal_simplified_invoice_id.is_simplified_invoice:
                pms_property.journal_simplified_invoice_id.is_simplified_invoice = True

    def _get_journal(self, is_simplified_invoice, room_ids=False):
        self.ensure_one()
        if is_simplified_invoice:
            if self.journal_simplified_invoice_id:
                return self.journal_simplified_invoice_id
        else:
            if self.journal_normal_invoice_id:
                return self.journal_normal_invoice_id
        journals = self.env["account.journal"].search(
            [
                ("type", "=", "sale"),
                ("is_simplified_invoice", "=", is_simplified_invoice),
                ("company_id", "=", self.company_id.id),
                "|",
                ("pms_property_ids", "in", self.id),
                ("pms_property_ids", "=", False),
            ]
        )
        if journals:
            if room_ids:
                journals = journals.filtered(
                    lambda j: not j.room_filter_ids
                    or any([room_id in j.room_filter_ids.ids for room_id in room_ids])
                )
            return journals[0]
        return False

    @api.model
    def _get_folio_default_journal(self, partner_invoice_id, room_ids=False):
        self.ensure_one()
        partner = self.env["res.partner"].browse(partner_invoice_id)
        # For simplified invoices
        if not partner or partner.id == self.env.ref("pms.various_pms_partner").id:
            return self._get_journal(is_simplified_invoice=True, room_ids=room_ids)
        # For normal invoices
        return self._get_journal(is_simplified_invoice=False, room_ids=room_ids)

    def _get_adr(self, start_date, end_date, domain=False):
        """
        Calculate monthly ADR for a property
        :param start_date: start date
        :param pms_property_id: pms property id
        :param domain: domain to filter reservations (channel, agencies, etc...)
        """
        self.ensure_one()
        domain = [] if not domain else domain
        domain.extend(
            [
                ("pms_property_id", "=", self.id),
                ("occupies_availability", "=", True),
                ("reservation_id.reservation_type", "=", "normal"),
                ("date", ">=", start_date),
                ("date", "<=", end_date),
            ]
        )
        group_adr = self.env["pms.reservation.line"].read_group(
            domain,
            ["price:avg"],
            ["date:day"],
        )
        if not len(group_adr):
            return 0
        adr = 0
        for day_adr in group_adr:
            adr += day_adr["price"]

        return round(adr / len(group_adr), 2)

    def _get_revpar(self, start_date, end_date, domain=False):
        """
        Calculate monthly revpar for a property only in INE rooms
        :param start_date: start date
        :param pms_property_id: pms property id
        :param domain: domain to filter reservations (channel, agencies, etc...)
        """
        self.ensure_one()
        domain = [] if not domain else domain
        domain.extend(
            [
                ("pms_property_id", "=", self.id),
                ("occupies_availability", "=", True),
                ("room_id.in_ine", "=", True),
                ("date", ">=", start_date),
                ("date", "<=", end_date),
            ]
        )
        price_domain = expression.AND(
            [domain, [("reservation_id.reservation_type", "=", "normal")]]
        )
        sum_group_price = self.env["pms.reservation.line"].read_group(
            price_domain,
            ["price"],
            [],
        )
        not_allowed_rooms_domain = expression.AND(
            [
                domain,
                [("reservation_id.reservation_type", "!=", "normal")],
            ]
        )
        count_room_days_not_allowed = len(
            self.env["pms.reservation.line"].search(not_allowed_rooms_domain)
        )
        date_range_days = (end_date - start_date).days + 1
        count_total_room_days = len(self.room_ids) * date_range_days
        count_available_room_days = count_total_room_days - count_room_days_not_allowed
        if not sum_group_price[0]["price"]:
            return 0
        revpar = round(sum_group_price[0]["price"] / count_available_room_days, 2)
        return revpar

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                "|",
                ("ref", "=ilike", name.split(" ")[0] + "%"),
                ("pms_property_code", "=ilike", name.split(" ")[0] + "%"),
                ("name", operator, name),
            ]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ["&", "!"] + domain[1:]
        return self._search(
            expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid
        )

    def name_get(self):
        result = []
        for record in self:
            if self.env.context.get("only_code", False) and record.pms_property_code:
                result.append((record.id, record.pms_property_code))
            elif (
                self.env.context.get("only_name", False) or not record.pms_property_code
            ):
                result.append((record.id, record.name))
            else:
                result.append(
                    (record.id, "[" + record.pms_property_code + "] " + record.name)
                )
        return result
