# Copyright 2019  Pablo Quesada
# Copyright 2019  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
import time

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

from odoo.addons.base.models.res_partner import _tz_get


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
        ondelete="cascade",
    )
    company_id = fields.Many2one(
        string="Company",
        help="The company that owns or operates this property.",
        comodel_name="res.company",
        required=True,
        check_pms_properties=True,
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
        comodel_name="ir.sequence",
    )
    reservation_sequence_id = fields.Many2one(
        string="Reservation Sequence",
        help="The sequence that formed the name of the reservation.",
        check_company=True,
        copy=False,
        comodel_name="ir.sequence",
    )
    checkin_sequence_id = fields.Many2one(
        string="Checkin Sequence",
        help="Field used to create the name of the checkin partner",
        check_company=True,
        copy=False,
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

    @api.depends_context(
        "checkin",
        "checkout",
        "room_type_id",
        "ubication_id",
        "capacity",
        "amenity_ids",
        "pricelist_id",
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

        for pms_property in self:
            free_rooms = pms_property.get_real_free_rooms(
                checkin, checkout, current_lines
            )
            if pricelist_id:
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
            if len(free_rooms) > 0:
                pms_property.free_room_ids = free_rooms.ids
            else:
                pms_property.free_room_ids = False

    def get_real_free_rooms(self, checkin, checkout, current_lines=False):
        self.ensure_one()
        Avail = self.env["pms.availability"]
        target_rooms = self.env["pms.room"].search([("pms_property_id", "=", self.id)])

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

        domain_avail = [
            ("date", ">=", checkin),
            ("date", "<=", checkout - datetime.timedelta(1)),
            ("pms_property_id", "=", self.id),
        ]

        if not current_lines:
            current_lines = []

        rooms_not_avail = (
            Avail.search(domain_avail)
            .reservation_line_ids.filtered(
                lambda l: l.occupies_availability and l.id and l.id not in current_lines
            )
            .room_id.ids
        )

        domain_rooms = [("id", "in", target_rooms.ids)]
        if rooms_not_avail:
            domain_rooms.append(
                ("id", "not in", rooms_not_avail),
            )
        return self.env["pms.room"].search(domain_rooms)

    @api.depends_context(
        "checkin",
        "checkout",
        "room_type_id",
        "ubication_id",
        "capacity",
        "amenity_ids",
        "pricelist_id",
        "current_lines",
    )
    def _compute_availability(self):
        self.ensure_one()
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
        current_lines = self.env.context.get("current_lines", False)
        pms_property = self.with_context(
            checkin=checkin,
            checkout=checkout,
            room_type_id=room_type_id,
            current_lines=current_lines,
            pricelist_id=pricelist_id,
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
        if pricelist and pricelist.availability_plan_id:
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
        self.availability = count_free_rooms

    @api.model
    def splitted_availability(
        self,
        checkin,
        checkout,
        pms_property_id,
        room_type_id=False,
        current_lines=False,
        pricelist=False,
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
            )

            if len(pms_property.free_room_ids) < 1:
                return False
        return True

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
        tz_property = self.tz
        dt = pytz.timezone(tz_property).localize(dt)
        dt = dt.replace(tzinfo=None)
        dt = pytz.timezone(self.env.user.tz).localize(dt)
        dt = dt.astimezone(pytz.utc)
        dt = dt.replace(tzinfo=None)
        return dt

    def _get_payment_methods(self):
        self.ensure_one()
        payment_methods = self.env["account.journal"].search(
            [
                "&",
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
        if "reservation_sequence_id" not in vals or not vals.get(
            "reservation_sequence_id"
        ):
            reservation_sequence = self.env["ir.sequence"].create(
                {
                    "name": "PMS Reservation " + name,
                    "code": "pms.reservation",
                    "prefix": "R/%(y)s",
                    "suffix": "%(sec)s",
                    "padding": 4,
                    "company_id": vals.get("company_id"),
                }
            )
            vals.update({"reservation_sequence_id": reservation_sequence.id})
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
