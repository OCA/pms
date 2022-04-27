# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import datetime
import time

import pytz
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models, modules
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

from odoo.addons.base.models.res_partner import _tz_get


def get_default_logo():
    with open(
        modules.get_module_resource("pms", "static/img", "property_logo.png"), "rb"
    ) as f:
        return base64.b64encode(f.read())


class PmsProperty(models.Model):
    _name = "pms.property"
    _description = "Property"
    _inherits = {"res.partner": "partner_id"}
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
        string="Arrival Hour", help="HH:mm Format", default="14:00"
    )
    default_departure_hour = fields.Char(
        string="Departure Hour", help="HH:mm Format", default="12:00"
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

    mail_information = fields.Html(
        string="Mail Information", help="Additional information of the mail"
    )

    privacy_policy = fields.Html(string="Privacy Policy", help="Mail privacy policy ")

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

    default_invoicing_policy = fields.Selection(
        string="Default Invoicing Policy",
        selection=[
            ("manual", "Manual"),
            ("checkout", "Checkout"),
            ("month_day", "Month Day Invoice"),
        ],
        default="manual",
    )

    margin_days_autoinvoice = fields.Integer(
        string="Margin Days",
        help="Days from Checkout to generate the invoice",
    )

    invoicing_month_day = fields.Integer(
        string="Invoicing Month Day",
        help="The day of the month to invoice",
    )

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
        string="Max Amount Simplified Invoice",
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
                            lambda x: x.room_type_id.id not in room_types_to_remove
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
            count_free_rooms = len(pms_property.free_room_ids)
            if current_lines and not isinstance(current_lines, list):
                current_lines = [current_lines]

            domain_rules = [
                ("date", ">=", checkin),
                ("date", "<=", checkout),
                ("pms_property_id", "=", pms_property.id),
            ]
            if room_type_id:
                domain_rules.append(("room_type_id", "=", room_type_id))

            pricelist = False
            if pricelist_id:
                pricelist = self.env["product.pricelist"].browse(pricelist_id)
            if pricelist and pricelist.availability_plan_id and not real_avail:
                domain_rules.append(
                    ("availability_plan_id", "=", pricelist.availability_plan_id.id)
                )
                rule_groups = self.env["pms.availability.plan.rule"].read_group(
                    domain_rules,
                    ["plan_avail:sum"],
                    ["date:day"],
                    lazy=False,
                )
                if len(rule_groups) > 0:
                    # If in the group per day, some room type has the sale blocked,
                    # we must subtract from that day the availability of that room type
                    for group in rule_groups:
                        items = self.env["pms.availability.plan.rule"].search(
                            group["__domain"]
                        )
                        for item in items:
                            if pricelist.availability_plan_id.any_rule_applies(
                                checkin, checkout, item
                            ):
                                group["plan_avail"] -= item.plan_avail
                    count_free_rooms = min(i["plan_avail"] for i in rule_groups)
            record.availability = count_free_rooms

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
                            "Alreay exist other property with this ref: %s (%s)",
                            duplicated.name,
                            duplicated.ref,
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
                            "Alreay exist other property with this code: %s (%s)",
                            duplicated.name,
                            duplicated.pms_property_code,
                        )
                    )

    @api.constrains("default_arrival_hour")
    def _check_arrival_hour(self):
        for record in self:
            try:
                time.strptime(record.default_arrival_hour, "%H:%M")
                return True
            except ValueError:
                raise ValidationError(
                    _(
                        "Format Arrival Hour (HH:MM) Error: %s",
                        record.default_arrival_hour,
                    )
                )

    @api.constrains("default_departure_hour")
    def _check_departure_hour(self):
        for record in self:
            try:
                time.strptime(record.default_departure_hour, "%H:%M")
                return True
            except ValueError:
                raise ValidationError(
                    _(
                        "Format Departure Hour (HH:MM) Error: %s",
                        record.default_departure_hour,
                    )
                )

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

    def _get_payment_methods(self, automatic_included=False):
        # We use automatic_included to True to see absolutely
        # all the journals with associated payments, if it is
        # false, we will only see those journals that can be used
        # to pay manually
        self.ensure_one()
        payment_methods = self.env["account.journal"].search(
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
        if not automatic_included:
            payment_methods = payment_methods.filtered(lambda p: p.allowed_pms_payments)
        return payment_methods

    @api.model
    def create(self, vals):
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
        record = super(PmsProperty, self).create(vals)
        return record

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

    @api.model
    def autoinvoicing(self, offset=0, with_delay=False, autocommit=False):
        """
        This method is used to invoicing automatically the folios
        and validate the draft invoices created by the folios
        """
        date_reference = fields.Date.today() - relativedelta(days=offset)
        # REVIEW: We clean the autoinvoice_date of the past draft invoices
        # to avoid blocking the autoinvoicing
        self.clean_date_on_past_draft_invoices(date_reference)
        # 1- Invoicing the folios
        folios = self.env["pms.folio"].search(
            [
                ("sale_line_ids.autoinvoice_date", "=", date_reference),
                ("invoice_status", "=", "to_invoice"),
                ("amount_total", ">", 0),
            ]
        )
        paid_folios = folios.filtered(lambda f: f.pending_amount <= 0)
        unpaid_folios = folios.filtered(lambda f: f.pending_amount > 0)
        folios_to_invoice = paid_folios
        # If the folio is unpaid we will auto invoice only the
        # not cancelled lines
        for folio in unpaid_folios:
            if any([res.state != "cancel" for res in folio.reservation_ids]):
                folios_to_invoice += folio
            else:
                folio.sudo().message_post(
                    body=_(
                        "Not invoiced due to pending amounts and cancelled reservations"
                    )
                )
        for folio in folios_to_invoice:
            if with_delay:
                self.with_delay().autoinvoice_folio(folio)
            else:
                self.autoinvoice_folio(folio)
        # 2- Validate the draft invoices created by the folios
        draft_invoices_to_post = self.env["account.move"].search(
            [
                ("state", "=", "draft"),
                ("invoice_date_due", "=", date_reference),
                ("folio_ids", "!=", False),
            ]
        )
        for invoice in draft_invoices_to_post:
            if with_delay:
                self.with_delay().autovalidate_folio_invoice(invoice)
            else:
                self.autovalidate_folio_invoice(invoice)

        # 3- Reverse the downpayment invoices that not was included in final invoice
        downpayments_invoices_to_reverse = self.env["account.move.line"].search(
            [
                ("move_id.state", "=", "posted"),
                ("folio_line_ids.is_downpayment", "=", True),
                ("folio_line_ids.qty_invoiced", ">", 0),
                ("folio_ids", "in", folios.ids),
            ]
        )
        downpayment_invoices = downpayments_invoices_to_reverse.mapped("move_id")
        if downpayment_invoices:
            for downpayment_invoice in downpayment_invoices:
                default_values_list = [
                    {
                        "ref": _(f'Reversal of: {move.name + " - " + move.ref}'),
                    }
                    for move in downpayment_invoice
                ]
                downpayment_invoice.with_context(
                    {"sii_refund_type": "I"}
                )._reverse_moves(default_values_list, cancel=True)
                downpayment_invoice.message_post(
                    body=_(
                        """
                           The downpayment invoice has been reversed
                           because it was not included in the final invoice
                        """
                    )
                )

        return True

    @api.model
    def clean_date_on_past_draft_invoices(self, date_reference):
        """
        This method is used to clean the date on past draft invoices
        """
        journal_ids = (
            self.env["account.journal"]
            .search(
                [
                    ("type", "=", "sale"),
                    ("pms_property_ids", "!=", False),
                ]
            )
            .ids
        )
        draft_invoices = self.env["account.move"].search(
            [
                ("state", "=", "draft"),
                ("invoice_date", "<", date_reference),
                ("journal_id", "in", journal_ids),
            ]
        )
        if draft_invoices:
            draft_invoices.write({"invoice_date": date_reference})
        return True

    def autovalidate_folio_invoice(self, invoice):
        try:
            with self.env.cr.savepoint():
                invoice.action_post()
        except Exception as e:
            invoice.message_post(body=_("Error in autovalidate invoice: " + str(e)))

    def autoinvoice_folio(self, folio):
        try:
            with self.env.cr.savepoint():
                # REVIEW: folio sale line "_compute_auotinvoice_date" sometimes
                # dont work in services (probably cache issue¿?), we ensure that the date is
                # set or recompute this
                for line in folio.sale_line_ids.filtered(
                    lambda l: not l.autoinvoice_date
                ):
                    line._compute_autoinvoice_date()
                invoices = folio.with_context(autoinvoice=True)._create_invoices(
                    grouped=True,
                    final=False,
                )
                downpayments = folio.sale_line_ids.filtered(
                    lambda l: l.is_downpayment and l.qty_invoiced > 0
                )
                for invoice in invoices:
                    if (
                        invoice.amount_total
                        > invoice.pms_property_id.max_amount_simplified_invoice
                        and invoice.journal_id.is_simplified_invoice
                    ):
                        hosts_to_invoice = (
                            invoice.folio_ids.partner_invoice_ids.filtered(
                                lambda p: p._check_enought_invoice_data()
                            ).mapped("id")
                        )
                        if hosts_to_invoice:
                            invoice.partner_id = hosts_to_invoice[0]
                            invoice.journal_id = (
                                invoice.pms_property_id.journal_normal_invoice_id
                            )
                        else:
                            mens = _(
                                "The total amount of the simplified invoice is higher than the "
                                "maximum amount allowed for simplified invoices, and dont have "
                                "enought data in hosts to create a normal invoice."
                            )
                            folio.sudo().message_post(body=mens)
                            raise ValidationError(mens)
                    for downpayment in downpayments.filtered(
                        lambda d: d.default_invoice_to == invoice.partner_id
                    ):
                        # If the downpayment invoice partner is the same that the
                        # folio partner, we include the downpayment in the normal invoice
                        invoice_down_payment_vals = downpayment._prepare_invoice_line(
                            sequence=max(invoice.invoice_line_ids.mapped("sequence"))
                            + 1,
                        )
                        invoice.write(
                            {"invoice_line_ids": [(0, 0, invoice_down_payment_vals)]}
                        )
                    invoice.action_post()
                # The downpayment invoices that not was included in final invoice, are reversed
                downpayment_invoices = (
                    downpayments.filtered(
                        lambda d: d.qty_invoiced > 0
                    ).invoice_lines.mapped("move_id")
                ).filtered(lambda i: i.is_simplified_invoice)
                if downpayment_invoices:
                    default_values_list = [
                        {
                            "ref": _(f'Reversal of: {move.name + " - " + move.ref}'),
                        }
                        for move in downpayment_invoices
                    ]
                    downpayment_invoices.with_context(
                        {"sii_refund_type": "I"}
                    )._reverse_moves(default_values_list, cancel=True)
        except Exception as e:
            folio.sudo().message_post(body=_("Error in autoinvoicing folio: " + str(e)))

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

    @api.model
    def _get_folio_default_journal(self, partner_invoice_id):
        self.ensure_one()
        partner = self.env["res.partner"].browse(partner_invoice_id)
        if (
            not partner
            or partner.id == self.env.ref("pms.various_pms_partner").id
            or (
                not partner._check_enought_invoice_data()
                and self._context.get("autoinvoice")
            )
        ):
            return self.journal_simplified_invoice_id
        return self.journal_normal_invoice_id

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
