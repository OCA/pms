import datetime

from odoo import api, fields, models
from odoo.osv import expression


class AvailabilityWizard(models.TransientModel):

    _name = "pms.massive.changes.wizard"
    _description = "Wizard for massive changes on Availability Plans & Pricelists."
    _check_pms_properties_auto = True

    pms_property_ids = fields.Many2many(
        string="Property",
        comodel_name="pms.property",
        default=lambda self: self.env["pms.property"].browse(
            self.env.user.get_active_property_ids()[0]
        ),
        check_pms_properties=True,
    )
    massive_changes_on = fields.Selection(
        string="On",
        selection=[
            ("pricelist", "Pricelist"),
            ("availability_plan", "Availability Plan"),
        ],
        required=True,
        default="availability_plan",
    )
    availability_plan_id = fields.Many2one(
        string="Availability Plan to apply massive changes",
        comodel_name="pms.availability.plan",
        check_pms_properties=True,
        # can be setted by context from availability plan detail
    )
    pricelist_id = fields.Many2one(
        string="Pricelist to apply massive changes",
        comodel_name="product.pricelist",
        check_pms_properties=True,
    )
    allowed_pricelist_ids = fields.One2many(
        string="Allowed pricelists",
        comodel_name="product.pricelist",
        compute="_compute_allowed_pricelist_ids",
    )
    start_date = fields.Date(
        string="From",
        required=True,
    )
    end_date = fields.Date(
        string="To",
        required=True,
    )
    room_type_id = fields.Many2one(
        string="Room Type",
        comodel_name="pms.room.type",
        check_pms_properties=True,
    )
    price = fields.Float(string="Price")
    min_quantity = fields.Float(string="Min. Quantity")

    min_stay = fields.Integer(
        string="Min. Stay",
        default=0,
    )
    min_stay_arrival = fields.Integer(
        string="Min. Stay Arrival",
        default=0,
    )
    max_stay = fields.Integer(
        string="Max. Stay",
        default=0,
    )
    max_stay_arrival = fields.Integer(
        string="Max. Stay Arrival",
        default=0,
    )
    closed = fields.Boolean(
        string="Closed",
        default=False,
    )
    closed_departure = fields.Boolean(
        string="Closed Departure",
        default=False,
    )
    closed_arrival = fields.Boolean(
        string="Closed Arrival",
        default=False,
    )
    quota = fields.Integer(
        string="Quota",
        help="Generic Quota assigned.",
        default=-1,
    )
    max_avail = fields.Integer(
        string="Max. Availability",
        help="Maximum simultaneous availability on own Booking Engine.",
        default=-1,
    )
    apply_on_monday = fields.Boolean(
        string="Apply Availability Rule on mondays",
        default=False,
    )
    apply_on_tuesday = fields.Boolean(
        string="Apply Availability Rule on tuesdays",
        default=False,
    )
    apply_on_wednesday = fields.Boolean(
        string="Apply Availability Rule on wednesdays",
        default=False,
    )
    apply_on_thursday = fields.Boolean(
        string="Apply Availability Rule on thursdays",
        default=False,
    )
    apply_on_friday = fields.Boolean(
        string="Apply Availability Rule on fridays",
        default=False,
    )
    apply_on_saturday = fields.Boolean(
        string="Apply Availability Rule on saturdays",
        default=False,
    )
    apply_on_sunday = fields.Boolean(
        string="Apply Availability Rule on sundays",
        default=False,
    )
    apply_on_all_week = fields.Boolean(
        string="Apply Availability Rule for the whole week",
        default=True,
    )
    apply_min_stay = fields.Boolean(
        string="Apply changes to Min. Stay",
        default=False,
    )

    apply_min_stay_arrival = fields.Boolean(
        string="Apply changes to Min. Stay Arrival",
        default=False,
    )

    apply_max_stay = fields.Boolean(
        string="Apply changes to Max. Stay",
        default=False,
    )

    apply_max_stay_arrival = fields.Boolean(
        string="Apply changes to Max. Stay Arrival",
        default=False,
    )

    apply_quota = fields.Boolean(
        string="Apply changes to Quota",
        default=False,
    )

    apply_max_avail = fields.Boolean(
        string="Apply changes to Max. Avail.",
        default=False,
    )

    apply_closed = fields.Boolean(
        string="Apply changes to Closed",
        default=False,
    )

    apply_closed_arrival = fields.Boolean(
        string="Apply changes to Closed Arrival",
        default=False,
    )

    apply_closed_departure = fields.Boolean(
        string="Apply changes to Closed Departure",
        default=False,
    )

    rules_to_overwrite = fields.One2many(
        string="Rule to Overwrite",
        readonly=True,
        store=False,
        comodel_name="pms.availability.plan.rule",
        compute="_compute_rules_to_overwrite",
    )
    pricelist_items_to_overwrite = fields.One2many(
        string="Pricelist Items to Override",
        readonly=True,
        store=False,
        comodel_name="product.pricelist.item",
        compute="_compute_pricelist_items_to_overwrite",
    )
    num_rules_to_overwrite = fields.Integer(
        string="Rules to overwrite on massive changes",
        readonly=True,
        store=False,
        compute="_compute_num_rules_to_overwrite",
    )
    num_pricelist_items_to_overwrite = fields.Integer(
        string="Pricelist items to overwrite on massive changes",
        compute="_compute_num_pricelist_items_to_overwrite",
        readonly=True,
        store=False,
    )
    avail_readonly = fields.Boolean(
        string="Avialability Readonly",
        default=lambda self: self._default_avail_readonly(),
    )
    pricelist_readonly = fields.Boolean(
        string="Pricelist Readonly",
        default=lambda self: self._default_pricelist_readonly(),
    )

    def _default_avail_readonly(self):
        return True if self._context.get("availability_plan_id") else False

    def _default_pricelist_readonly(self):
        return True if self._context.get("pricelist_id") else False

    @api.depends("massive_changes_on")
    def _compute_allowed_pricelist_ids(self):
        for record in self:
            record.allowed_pricelist_ids = self.env["product.pricelist"].search(
                [
                    ("pricelist_type", "=", "daily"),
                ]
            )

    @api.depends(
        "start_date",
        "end_date",
        "room_type_id",
        "apply_on_monday",
        "apply_on_tuesday",
        "apply_on_wednesday",
        "apply_on_thursday",
        "apply_on_friday",
        "apply_on_saturday",
        "apply_on_sunday",
        "apply_on_all_week",
        "availability_plan_id",
        "apply_quota",
        "apply_max_avail",
        "apply_min_stay",
        "apply_min_stay_arrival",
        "apply_max_stay",
        "apply_max_stay_arrival",
        "apply_closed",
        "apply_closed_arrival",
        "apply_closed_departure",
        "min_stay",
        "max_stay",
        "min_stay_arrival",
        "max_stay_arrival",
        "closed",
        "closed_arrival",
        "closed_departure",
        "quota",
        "max_avail",
    )
    def _compute_rules_to_overwrite(self):
        for record in self:

            if not record.availability_plan_id and self._context.get(
                "availability_plan_id"
            ):
                record.availability_plan_id = self._context.get("availability_plan_id")
                record.massive_changes_on = "availability_plan"

            if record.availability_plan_id:
                domain = [
                    ("availability_plan_id", "=", record.availability_plan_id.id),
                ]

                if record.room_type_id:
                    domain.append(("room_type_id", "=", record.room_type_id.id))
                if record.start_date:
                    domain.append(("date", ">=", record.start_date))
                if record.end_date:
                    domain.append(("date", "<=", record.end_date))

                domain_overwrite = self.build_domain_rules()
                if len(domain_overwrite):
                    if len(domain_overwrite) == 1:
                        domain.append(domain_overwrite[0][0])
                    else:
                        domain_overwrite = expression.OR(domain_overwrite)
                        domain.extend(domain_overwrite)

                week_days_to_apply = (
                    record.apply_on_monday,
                    record.apply_on_tuesday,
                    record.apply_on_wednesday,
                    record.apply_on_thursday,
                    record.apply_on_friday,
                    record.apply_on_saturday,
                    record.apply_on_sunday,
                )
                if record.start_date and record.end_date:
                    rules = self.env["pms.availability.plan.rule"].search(domain)
                    if (
                        not record.apply_on_all_week
                        and record.start_date
                        and record.end_date
                    ):
                        record.rules_to_overwrite = rules.filtered(
                            lambda x: week_days_to_apply[x.date.timetuple()[6]]
                        )
                    else:
                        record.rules_to_overwrite = rules
                else:
                    record.rules_to_overwrite = False
            else:
                record.rules_to_overwrite = False

    @api.depends(
        "start_date",
        "end_date",
        "room_type_id",
        "apply_on_monday",
        "apply_on_tuesday",
        "apply_on_wednesday",
        "apply_on_thursday",
        "apply_on_friday",
        "apply_on_saturday",
        "apply_on_sunday",
        "apply_on_all_week",
        "pricelist_id",
    )
    def _compute_pricelist_items_to_overwrite(self):
        for record in self:

            if not record.pricelist_id and self._context.get("pricelist_id"):
                record.pricelist_id = self._context.get("pricelist_id")
                record.massive_changes_on = "pricelist"

            if record.pricelist_id:
                domain = [
                    ("pricelist_id", "=", record.pricelist_id.id),
                    "|",
                    ("pms_property_ids", "=", False),
                    ("pms_property_ids", "in", record.pms_property_ids.ids),
                ]

                if record.start_date:
                    domain.append(("date_start_overnight", ">=", record.start_date))
                if record.end_date:
                    domain.append(("date_end_overnight", "<=", record.end_date))

                if record.room_type_id:
                    domain.append(
                        (
                            "product_tmpl_id",
                            "=",
                            record.room_type_id.product_id.product_tmpl_id.id,
                        )
                    )

                week_days_to_apply = (
                    record.apply_on_monday,
                    record.apply_on_tuesday,
                    record.apply_on_wednesday,
                    record.apply_on_thursday,
                    record.apply_on_friday,
                    record.apply_on_saturday,
                    record.apply_on_sunday,
                )

                if record.start_date and record.end_date:
                    items = self.env["product.pricelist.item"].search(domain)
                    if (
                        not record.apply_on_all_week
                        and record.start_date
                        and record.end_date
                    ):
                        record.pricelist_items_to_overwrite = items.filtered(
                            lambda x: week_days_to_apply[
                                x.date_end_overnight.timetuple()[6]
                            ]
                        )
                    else:
                        record.pricelist_items_to_overwrite = items
                else:
                    record.pricelist_items_to_overwrite = False
            else:
                record.pricelist_items_to_overwrite = False

    @api.depends(
        "rules_to_overwrite",
    )
    def _compute_num_rules_to_overwrite(self):
        for record in self:
            self.num_rules_to_overwrite = len(record.rules_to_overwrite)

    @api.depends(
        "pricelist_items_to_overwrite",
    )
    def _compute_num_pricelist_items_to_overwrite(self):
        for record in self:
            self.num_pricelist_items_to_overwrite = len(
                record.pricelist_items_to_overwrite
            )

    def build_domain_rules(self):
        for record in self:
            domain_overwrite = []
            if record.apply_min_stay:
                domain_overwrite.append([("min_stay", "!=", record.min_stay)])
            if record.apply_max_stay:
                domain_overwrite.append([("max_stay", "!=", record.max_stay)])
            if record.apply_min_stay_arrival:
                domain_overwrite.append(
                    [("min_stay_arrival", "!=", record.min_stay_arrival)]
                )
            if record.apply_max_stay_arrival:
                domain_overwrite.append(
                    [("max_stay_arrival", "!=", record.max_stay_arrival)]
                )
            if record.apply_quota:
                domain_overwrite.append([("quota", "!=", record.quota)])
            if record.apply_max_avail:
                domain_overwrite.append([("max_avail", "!=", record.max_avail)])
            if record.apply_closed:
                domain_overwrite.append([("closed", "!=", record.closed)])
            if record.apply_closed_arrival:
                domain_overwrite.append(
                    [("closed_arrival", "!=", record.closed_arrival)]
                )
            if record.apply_closed_departure:
                domain_overwrite.append(
                    [("closed_departure", "!=", record.closed_departure)]
                )
            return domain_overwrite

    def apply_massive_changes(self):

        for record in self:
            record.pricelist_items_to_overwrite.unlink()
            week_days_to_apply = (
                record.apply_on_monday,
                record.apply_on_tuesday,
                record.apply_on_wednesday,
                record.apply_on_thursday,
                record.apply_on_friday,
                record.apply_on_saturday,
                record.apply_on_sunday,
            )

            # dates between start and end (both included)
            for date in [
                record.start_date + datetime.timedelta(days=x)
                for x in range(0, (record.end_date - record.start_date).days + 1)
            ]:

                if (
                    not record.apply_on_all_week
                    and not week_days_to_apply[date.timetuple()[6]]
                ):
                    continue

                if not record.room_type_id:
                    room_types = self.env["pms.room.type"].search(
                        [
                            "|",
                            ("pms_property_ids", "=", False),
                            ("pms_property_ids", "in", record.pms_property_ids.ids),
                        ]
                    )
                else:
                    room_types = [record.room_type_id]
                for room_type in room_types:
                    for pms_property in record.pms_property_ids:
                        if record.massive_changes_on == "pricelist":

                            self.env["product.pricelist.item"].create(
                                {
                                    "pricelist_id": record.pricelist_id.id,
                                    "date_start_overnight": date,
                                    "date_end_overnight": date,
                                    "compute_price": "fixed",
                                    "applied_on": "0_product_variant",
                                    "product_id": room_type.product_id.id,
                                    "fixed_price": record.price,
                                    "min_quantity": record.min_quantity,
                                    "pms_property_ids": [pms_property.id],
                                }
                            )
                        else:
                            avail_plan_id = record.availability_plan_id.id
                            vals = {}
                            vals.update(
                                {"min_stay": record.min_stay}
                                if record.apply_min_stay
                                else {}
                            )
                            vals.update(
                                {"min_stay_arrival": record.min_stay_arrival}
                                if record.apply_min_stay_arrival
                                else {}
                            )
                            vals.update(
                                {"max_stay": record.max_stay}
                                if record.apply_max_stay
                                else {}
                            )

                            vals.update(
                                {"max_stay_arrival": record.max_stay_arrival}
                                if record.apply_max_stay_arrival
                                else {}
                            )
                            vals.update(
                                {"quota": record.quota} if record.apply_quota else {}
                            )
                            vals.update(
                                {"max_avail": record.max_avail}
                                if record.apply_max_avail
                                else {}
                            )

                            vals.update(
                                {"closed": record.closed} if record.apply_closed else {}
                            )
                            vals.update(
                                {"closed_arrival": record.closed_arrival}
                                if record.apply_closed_arrival
                                else {}
                            )
                            vals.update(
                                {"closed_departure": record.closed_departure}
                                if record.apply_closed_departure
                                else {}
                            )

                            if date in record.rules_to_overwrite.mapped(
                                "date"
                            ) and room_type in record.rules_to_overwrite.mapped(
                                "room_type_id"
                            ):

                                overwrite = record.rules_to_overwrite.search(
                                    [
                                        ("room_type_id", "=", room_type.id),
                                        ("date", "=", date),
                                    ]
                                )
                                overwrite.write(vals)
                            else:
                                self.env["pms.availability.plan.rule"].create(
                                    {
                                        "availability_plan_id": avail_plan_id,
                                        "date": date,
                                        "room_type_id": room_type.id,
                                        "quota": record.quota,
                                        "max_avail": record.max_avail,
                                        "min_stay": record.min_stay,
                                        "min_stay_arrival": record.min_stay_arrival,
                                        "max_stay": record.max_stay,
                                        "max_stay_arrival": record.max_stay_arrival,
                                        "closed": record.closed,
                                        "closed_arrival": record.closed_arrival,
                                        "closed_departure": record.closed_departure,
                                        "pms_property_id": pms_property.id,
                                    }
                                )
            if (
                record.massive_changes_on == "pricelist"
                and not record.pricelist_readonly
            ):
                action = self.env.ref("product.product_pricelist_action2").read()[0]
                action["views"] = [
                    (self.env.ref("pms.product_pricelist_view_form").id, "form")
                ]
                action["res_id"] = record.pricelist_id.id
                return action
            if (
                record.massive_changes_on == "availability_plan"
                and not record.avail_readonly
            ):
                action = self.env.ref("pms.availability_action").read()[0]
                action["views"] = [
                    (self.env.ref("pms.availability_view_form").id, "form")
                ]
                action["res_id"] = record.availability_plan_id.id
                return action
