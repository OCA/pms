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
        required=True,
    )
    massive_changes_on = fields.Selection(
        string="On",
        selection=[
            ("pricelist", "Pricelist"),
            ("availability_plan", "Availability Plan"),
        ],
        default=lambda self: "availability_plan"
        if self._context.get("availability_plan_id")
        else "pricelist"
        if self._context.get("pricelist_id")
        else "availability_plan",
        required=True,
    )

    availability_plan_ids = fields.Many2many(
        comodel_name="pms.availability.plan",
        string="Availability Plan to apply massive changes",
        check_pms_properties=True,
    )

    pricelist_ids = fields.Many2many(
        comodel_name="product.pricelist",
        string="Pricelist to apply massive changes",
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

    apply_pricelists_on = fields.Selection(
        string="Apply pricelists on",
        selection=[
            ("room_types", "Room Types"),
            ("board_services", "Board Services"),
            ("service", "Service"),
        ],
        default="room_types",
    )

    room_type_ids = fields.Many2many(
        comodel_name="pms.room.type",
        string="Room Type",
        check_pms_properties=True,
        compute="_compute_room_type_ids",
        readonly=False,
        store=True,
    )

    board_service_room_type_ids = fields.Many2many(
        string="Room type's board services",
        comodel_name="pms.board.service.room.type",
        check_pms_properties=True,
        compute="_compute_board_service_room_type_ids",
        readonly=False,
        store=True,
    )

    board_service = fields.Many2one(
        string="Board service",
        comodel_name="product.product",
        check_pms_properties=True,
        domain="[('id', 'in',allowed_board_services)]",
    )

    allowed_board_services = fields.Many2many(
        string="Allowed services",
        comodel_name="product.product",
        compute="_compute_allowed_board_services",
        readonly=False,
        store=True,
    )
    service = fields.Many2one(
        string="Service",
        comodel_name="product.product",
        check_pms_properties=True,
        compute="_compute_service",
        readonly=False,
        store=True,
    )
    date_types = fields.Selection(
        string="Date types",
        selection=[
            ("sale_dates", "Sale Dates"),
            ("consumption_dates", "Consumption Dates"),
        ],
        default="consumption_dates",
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

    @api.depends("apply_pricelists_on")
    def _compute_room_type_ids(self):
        for record in self:
            if (
                record.apply_pricelists_on == "board_services"
                or record.apply_pricelists_on == "service"
            ):
                record.room_type_ids = False

    @api.depends("apply_pricelists_on", "board_service")
    def _compute_board_service_room_type_ids(self):
        for record in self:
            if (
                record.apply_pricelists_on == "room_types"
                or record.apply_pricelists_on == "service"
            ):
                record.board_service_room_type_ids = False
                record.board_service = False
            else:
                if not record.board_service_room_type_ids:
                    allowed_board_service_room_type_ids = []
                    all_board_service_room_type_ids = self.env[
                        "pms.board.service.room.type"
                    ].search([])
                    if record.board_service:
                        for (
                            board_service_room_type_id
                        ) in all_board_service_room_type_ids:
                            if (
                                record.board_service
                                in board_service_room_type_id.board_service_line_ids.mapped(
                                    "product_id"
                                )
                            ):
                                allowed_board_service_room_type_ids.append(
                                    board_service_room_type_id.id
                                )
                    else:
                        allowed_board_service_room_type_ids = (
                            all_board_service_room_type_ids.ids
                        )
                    domain = []
                    if allowed_board_service_room_type_ids:
                        domain.append(("id", "in", allowed_board_service_room_type_ids))
                    record.board_service_room_type_ids = (
                        self.env["pms.board.service.room.type"].search(domain)
                        if domain
                        else False
                    )

    @api.depends("apply_pricelists_on")
    def _compute_service(self):
        for record in self:
            if (
                record.apply_pricelists_on == "board_services"
                or record.apply_pricelists_on == "room_types"
            ):
                record.service = False

    @api.depends("board_service_room_type_ids")
    def _compute_allowed_board_services(self):
        for record in self:
            if not record.board_service_room_type_ids:
                record.allowed_board_services = (
                    self.env["pms.board.service.room.type"]
                    .search([])
                    .board_service_line_ids.mapped("product_id")
                )
            else:
                product_ids = []
                for bs_room_type_id in record.board_service_room_type_ids:
                    tmp_list = bs_room_type_id.board_service_line_ids.mapped(
                        "product_id"
                    ).ids

                    product_ids = (
                        tmp_list
                        if not product_ids
                        else product_ids
                        if record.board_service_room_type_ids
                        else list(set(tmp_list) & set(product_ids))
                    )

                record.allowed_board_services = self.env["product.product"].search(
                    [
                        (
                            "id",
                            "in",
                            product_ids,
                        )
                    ]
                )

    def _rules_to_overwrite_by_plans(self, availability_plans):
        self.ensure_one()
        domain = [
            ("availability_plan_id", "in", availability_plans.ids),
        ]

        if self.room_type_ids:
            domain.append(("room_type_id", "in", self.room_type_ids.ids))
        if self.start_date:
            domain.append(("date", ">=", self.start_date))
        if self.end_date:
            domain.append(("date", "<=", self.end_date))

        domain_overwrite = self.build_domain_rules()
        if len(domain_overwrite):
            if len(domain_overwrite) == 1:
                domain.append(domain_overwrite[0][0])
            else:
                domain_overwrite = expression.OR(domain_overwrite)
                domain.extend(domain_overwrite)

        rules = self.env["pms.availability.plan.rule"]
        if self.start_date and self.end_date:
            rules = rules.search(domain)
            if not self.apply_on_all_week and self.start_date and self.end_date:
                week_days_to_apply = (
                    self.apply_on_monday,
                    self.apply_on_tuesday,
                    self.apply_on_wednesday,
                    self.apply_on_thursday,
                    self.apply_on_friday,
                    self.apply_on_saturday,
                    self.apply_on_sunday,
                )
                rules = rules.filtered(
                    lambda x: week_days_to_apply[x.date.timetuple()[6]]
                )

        return rules

    @api.depends(
        "start_date",
        "end_date",
        "room_type_ids",
        "apply_on_monday",
        "apply_on_tuesday",
        "apply_on_wednesday",
        "apply_on_thursday",
        "apply_on_friday",
        "apply_on_saturday",
        "apply_on_sunday",
        "apply_on_all_week",
        "availability_plan_ids",
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
            if not record.availability_plan_ids and self._context.get(
                "availability_plan_id"
            ):
                record.availability_plan_ids = [
                    (4, self._context.get("availability_plan_id"))
                ]
                record.massive_changes_on = "availability_plan"

            record.rules_to_overwrite = record._rules_to_overwrite_by_plans(
                record.availability_plan_ids
            )

    @api.depends(
        "start_date",
        "end_date",
        "room_type_ids",
        "board_service_room_type_ids",
        "board_service",
        "service",
        "apply_pricelists_on",
        "date_types",
        "apply_on_monday",
        "apply_on_tuesday",
        "apply_on_wednesday",
        "apply_on_thursday",
        "apply_on_friday",
        "apply_on_saturday",
        "apply_on_sunday",
        "apply_on_all_week",
        "pricelist_ids",
        "pms_property_ids",
    )
    def _compute_pricelist_items_to_overwrite(self):
        for record in self:
            if not record.pricelist_ids and self._context.get("pricelist_id"):
                record.pricelist_ids = [(4, self._context.get("pricelist_id"))]
                record.massive_changes_on = "pricelist"

            if (
                record.pricelist_ids
                and record.start_date
                and record.end_date
                and record.pms_property_ids
            ):
                domain = [
                    ("pricelist_id", "in", record.pricelist_ids.ids),
                    "|",
                    ("pms_property_ids", "=", False),
                    ("pms_property_ids", "in", record.pms_property_ids.ids),
                ]

                if record.date_types == "sale_dates":
                    domain.append(
                        (
                            "date_start",
                            ">=",
                            datetime.datetime.combine(
                                record.start_date, datetime.datetime.min.time()
                            ),
                        )
                    )
                    domain.append(
                        (
                            "date_start",
                            "<=",
                            datetime.datetime.combine(
                                record.end_date, datetime.datetime.max.time()
                            ),
                        )
                    )
                elif record.date_types == "consumption_dates":
                    domain.append(("date_start_consumption", ">=", record.start_date))
                    domain.append(("date_end_consumption", "<=", record.end_date))

                product_ids = self.generate_product_ids_to_filter(
                    record.apply_pricelists_on,
                    record.room_type_ids,
                    record.board_service_room_type_ids,
                    record.board_service,
                    record.service,
                )
                if product_ids:
                    domain.append(
                        (
                            "product_id",
                            "in",
                            product_ids,
                        )
                    )
                if record.board_service_room_type_ids:
                    domain.append(
                        (
                            "board_service_room_type_id",
                            "in",
                            record.board_service_room_type_ids.ids,
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
                        items_filtered = False
                        if record.date_types == "consumption_dates":
                            items_filtered = items.filtered(
                                lambda x: x.date_end_consumption
                                and week_days_to_apply[
                                    x.date_end_consumption.timetuple()[6]
                                ]
                            )
                        elif record.date_types == "sale_dates":
                            items_filtered = items.filtered(
                                lambda x: x.date_end
                                and week_days_to_apply[x.date_end.date().timetuple()[6]]
                            )
                        record.pricelist_items_to_overwrite = items_filtered
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

    @api.model
    def generate_product_ids_to_filter(
        self,
        apply_pricelists_on,
        room_type_ids,
        board_service_room_type_ids,
        board_service,
        service,
    ):
        product_ids = False
        all_room_type_ids = self.env["pms.room.type"].search([]).ids

        if apply_pricelists_on == "room_types":
            room_type_ids = room_type_ids.ids
            if not room_type_ids:
                room_type_ids = all_room_type_ids
            product_ids = (
                self.env["pms.room.type"]
                .search([("id", "in", room_type_ids)])
                .mapped("product_id")
                .ids
            )
        elif apply_pricelists_on == "board_services":
            if board_service:
                product_ids = [board_service.id]
            elif not board_service_room_type_ids and not board_service:
                product_ids = (
                    self.env["pms.board.service.room.type"]
                    .search([])
                    .board_service_line_ids.mapped("product_id")
                    .ids
                )
            else:
                bsrti = board_service_room_type_ids
                product_ids = bsrti.board_service_line_ids.mapped("product_id").ids

        elif apply_pricelists_on == "service":
            domain = []
            product_ids_board_services = (
                self.env["pms.board.service.room.type"]
                .search([])
                .board_service_line_ids.mapped("product_id")
                .ids
            )
            if product_ids_board_services:
                domain.append(("id", "not in", product_ids_board_services))
            if service:
                domain.append(("id", "=", service.id))
            product_ids = self.env["product.product"].search(domain).ids

        return product_ids

    @api.model
    def generate_dates_vals(
        self,
        date_types,
        vals,
        date,
    ):
        if date_types == "sale_dates":
            vals["date_start"] = datetime.datetime.combine(
                date, datetime.datetime.min.time()
            )
            vals["date_end"] = datetime.datetime.combine(
                date, datetime.datetime.max.time()
            )
        else:
            vals["date_start_consumption"] = date
            vals["date_end_consumption"] = date
        return vals

    @api.model
    def create_pricelists_items_room_types(
        self,
        room_types,
        pricelist_ids,
        price,
        min_quantity,
        pms_property,
        date,
        date_types,
    ):
        new_items = []
        for room_type in room_types:
            for pricelist in pricelist_ids:
                vals = {
                    "pricelist_id": pricelist.id,
                    "compute_price": "fixed",
                    "applied_on": "0_product_variant",
                    "product_id": room_type.product_id.id,
                    "fixed_price": price,
                    "min_quantity": min_quantity,
                    "pms_property_ids": [pms_property.id],
                }
                vals = self.generate_dates_vals(date_types, vals, date)

                pricelist_item = self.env["product.pricelist.item"].create(vals)
                new_items.append(pricelist_item.id)
        return new_items

    @api.model
    def create_pricelists_items_board_services(
        self,
        board_service_room_type_ids,
        pricelist_ids,
        board_service,
        price,
        min_quantity,
        pms_property,
        date_types,
        date,
    ):
        new_items = []
        for bs_room_type in board_service_room_type_ids:
            for pricelist in pricelist_ids:
                if board_service:
                    vals = {
                        "pricelist_id": pricelist.id,
                        "compute_price": "fixed",
                        "applied_on": "0_product_variant",
                        "product_id": board_service.id,
                        "board_service_room_type_id": bs_room_type.id,
                        "fixed_price": price,
                        "min_quantity": min_quantity,
                        "pms_property_ids": [pms_property.id],
                    }
                    vals = self.generate_dates_vals(date_types, vals, date)

                    pricelist_item = self.env["product.pricelist.item"].create(vals)
                    new_items.append(pricelist_item.id)

                else:
                    for (
                        board_service_line
                    ) in bs_room_type.pms_board_service_id.board_service_line_ids:
                        vals = {
                            "pricelist_id": pricelist.id,
                            "compute_price": "fixed",
                            "applied_on": "0_product_variant",
                            "product_id": board_service_line.product_id.id,
                            "board_service_room_type_id": bs_room_type.id,
                            "fixed_price": price,
                            "min_quantity": min_quantity,
                            "pms_property_ids": [pms_property.id],
                        }
                        vals = self.generate_dates_vals(date_types, vals, date)

                        pricelist_item = self.env["product.pricelist.item"].create(vals)
                        new_items.append(pricelist_item.id)
        return new_items

    @api.model
    def create_availability_plans_rules(
        self,
        room_types,
        availability_plan_ids,
        min_stay,
        apply_min_stay,
        min_stay_arrival,
        apply_min_stay_arrival,
        max_stay,
        apply_max_stay,
        max_stay_arrival,
        apply_max_stay_arrival,
        quota,
        apply_quota,
        max_avail,
        apply_max_avail,
        closed,
        apply_closed,
        closed_arrival,
        apply_closed_arrival,
        closed_departure,
        apply_closed_departure,
        date,
        rules_to_overwrite,
        pms_property,
    ):
        new_items = []
        for room_type in room_types:
            for avail_plan_id in availability_plan_ids:
                vals = {}
                vals.update({"min_stay": min_stay} if apply_min_stay else {})
                vals.update(
                    {"min_stay_arrival": min_stay_arrival}
                    if apply_min_stay_arrival
                    else {}
                )
                vals.update({"max_stay": max_stay} if apply_max_stay else {})

                vals.update(
                    {"max_stay_arrival": max_stay_arrival}
                    if apply_max_stay_arrival
                    else {}
                )
                vals.update({"quota": quota} if apply_quota else {})
                vals.update({"max_avail": max_avail} if apply_max_avail else {})

                vals.update({"closed": closed} if apply_closed else {})
                vals.update(
                    {"closed_arrival": closed_arrival} if apply_closed_arrival else {}
                )
                vals.update(
                    {"closed_departure": closed_departure}
                    if apply_closed_departure
                    else {}
                )

                if date in rules_to_overwrite.mapped(
                    "date"
                ) and room_type in rules_to_overwrite.mapped("room_type_id"):
                    overwrite = rules_to_overwrite.search(
                        [
                            ("room_type_id", "=", room_type.id),
                            ("date", "=", date),
                        ]
                    )
                    overwrite.write(vals)
                    new_items.append(overwrite.id)
                else:
                    plan_rule = self.env["pms.availability.plan.rule"].create(
                        {
                            "availability_plan_id": avail_plan_id.id,
                            "date": date,
                            "room_type_id": room_type.id,
                            "quota": quota,
                            "max_avail": max_avail,
                            "min_stay": min_stay,
                            "min_stay_arrival": min_stay_arrival,
                            "max_stay": max_stay,
                            "max_stay_arrival": max_stay_arrival,
                            "closed": closed,
                            "closed_arrival": closed_arrival,
                            "closed_departure": closed_departure,
                            "pms_property_id": pms_property.id,
                        }
                    )
                    new_items.append(plan_rule.id)

        return new_items

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
            items = []
            for date in [
                record.start_date + datetime.timedelta(days=x)
                for x in range(0, (record.end_date - record.start_date).days + 1)
            ]:

                if (
                    not record.apply_on_all_week
                    and not week_days_to_apply[date.timetuple()[6]]
                ):
                    continue

                if not record.room_type_ids:
                    room_types = self.env["pms.room.type"].search(
                        [
                            "|",
                            ("pms_property_ids", "=", False),
                            ("pms_property_ids", "in", record.pms_property_ids.ids),
                        ]
                    )
                else:
                    room_types = record.room_type_ids

                for pms_property in record.pms_property_ids:
                    if (
                        record.massive_changes_on == "pricelist"
                        and record.apply_pricelists_on == "room_types"
                    ):
                        new_items = self.create_pricelists_items_room_types(
                            room_types,
                            record.pricelist_ids,
                            record.price,
                            record.min_quantity,
                            pms_property,
                            date,
                            record.date_types,
                        )
                        items = items + new_items if new_items else items

                    elif (
                        record.massive_changes_on == "pricelist"
                        and record.apply_pricelists_on == "board_services"
                    ):
                        new_items = self.create_pricelists_items_board_services(
                            record.board_service_room_type_ids,
                            record.pricelist_ids,
                            record.board_service,
                            record.price,
                            record.min_quantity,
                            pms_property,
                            record.date_types,
                            date,
                        )
                        items = items + new_items if new_items else items

                    elif (
                        record.massive_changes_on == "pricelist"
                        and record.apply_pricelists_on == "service"
                    ):
                        for pricelist in record.pricelist_ids:
                            if record.service:
                                vals = {
                                    "pricelist_id": pricelist.id,
                                    "compute_price": "fixed",
                                    "applied_on": "0_product_variant",
                                    "product_id": record.service.id,
                                    "fixed_price": record.price,
                                    "min_quantity": record.min_quantity,
                                    "pms_property_ids": [pms_property.id],
                                }
                                vals = self.generate_dates_vals(
                                    record.date_types, vals, date
                                )

                                pricelist_item = self.env[
                                    "product.pricelist.item"
                                ].create(vals)
                                items.append(pricelist_item.id)
                    elif record.massive_changes_on == "availability_plan":

                        new_items = self.create_availability_plans_rules(
                            room_types,
                            record.availability_plan_ids,
                            record.min_stay,
                            record.apply_min_stay,
                            record.min_stay_arrival,
                            record.apply_min_stay_arrival,
                            record.max_stay,
                            record.apply_max_stay,
                            record.max_stay_arrival,
                            record.apply_max_stay_arrival,
                            record.quota,
                            record.apply_quota,
                            record.max_avail,
                            record.apply_max_avail,
                            record.closed,
                            record.apply_closed,
                            record.closed_arrival,
                            record.apply_closed_arrival,
                            record.closed_departure,
                            record.apply_closed_departure,
                            date,
                            record.rules_to_overwrite,
                            pms_property,
                        )
                        items = items + new_items if new_items else items
            if (
                record.massive_changes_on == "pricelist"
                and not record.pricelist_readonly
            ):
                action = {
                    "view": self.env.ref("pms.product_pricelist_item_action2").read()[0]
                }
                action["view"]["domain"] = [("id", "in", items)]
                return action["view"]

            if (
                record.massive_changes_on == "availability_plan"
                and not record.avail_readonly
            ):
                action = {
                    "view": self.env.ref(
                        "pms.availability_plan_rule_view_tree_action"
                    ).read()[0]
                }
                action["view"]["domain"] = [("id", "in", items)]
                return action["view"]
