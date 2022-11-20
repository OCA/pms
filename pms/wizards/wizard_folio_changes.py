from datetime import timedelta

from odoo import api, fields, models


class WizardFolioChanges(models.TransientModel):

    _name = "wizard.folio.changes"
    _description = "Folio Changes"

    folio_id = fields.Many2one(
        string="Folio",
        default=lambda self: self._default_folio_id(),
        comodel_name="pms.folio",
    )
    modification_type = fields.Selection(
        string="Modification Type",
        selection=[
            ("reservations", "Reservations"),
            ("dates", "Dates"),
            ("services", "Services Prices"),
        ],
        default="reservations",
    )
    room_type_filter_ids = fields.Many2many(
        string="Room types",
        default=lambda self: self._default_room_type_filter_ids(),
        comodel_name="pms.room.type",
        relation="folio_changes_room_type_rel",
        column1="folio_changes_id",
        column2="room_type_ids",
        domain="[('id', 'in', allowed_room_type_ids)]",
    )
    allowed_room_type_ids = fields.Many2many(
        string="Allowed Room Types",
        comodel_name="pms.room.type",
        relation="folio_changes_allowed_room_type_rel",
        column1="folio_changes_id",
        column2="allowed_room_type_ids",
        compute="_compute_allowed_room_type_ids",
    )
    change_from_date = fields.Date(
        string="Apply From",
        default=lambda self: self.default_change_from_date(),
    )
    change_to_date = fields.Date(
        string="Apply To",
        default=lambda self: self.default_change_to_date(),
    )
    reservation_ids = fields.Many2many(
        string="Reservations",
        default=lambda self: self._default_reservation_ids(),
        comodel_name="pms.reservation",
        relation="folio_changes_reservation_rel",
        column1="folio_changes_id",
        column2="reservation_ids",
        domain="[('id', 'in', allowed_reservation_ids)]",
    )
    allowed_reservation_ids = fields.Many2many(
        string="Allowed Reservations",
        comodel_name="pms.reservation",
        relation="folio_changes_allowed_reservation_rel",
        column1="folio_changes_id",
        column2="allowed_reservation_ids",
        compute="_compute_allowed_reservation_ids",
    )
    service_ids = fields.Many2many(
        string="Services",
        default=lambda self: self._default_service_ids(),
        comodel_name="pms.service",
        relation="folio_changes_service_rel",
        column1="folio_changes_id",
        column2="service_ids",
        domain="[('id', 'in', allowed_service_ids)]",
    )
    allowed_service_ids = fields.Many2many(
        string="Allowed Services",
        comodel_name="pms.service",
        relation="folio_changes_allowed_service_rel",
        column1="folio_changes_id",
        column2="allowed_service_ids",
        compute="_compute_allowed_service_ids",
    )
    apply_new_checkin = fields.Boolean(
        string="Apply Checkin Update",
        default=False,
    )
    new_checkin = fields.Date(
        string="New Checkin",
        default=lambda self: self.default_change_new_checkin(),
    )

    apply_new_checkout = fields.Boolean(
        string="Apply Checkout Update",
        default=False,
    )
    new_checkout = fields.Date(
        string="New Checkout",
        default=lambda self: self.default_change_new_checkout(),
    )
    nights = fields.Integer(
        string="Nights",
        compute="_compute_nights",
    )
    dates_incongruence = fields.Boolean(
        string="Dates incrongruence",
        help="Indicates that there are reservations with different checkin and/or checkout",
        compute="_compute_dates_incongruence",
        store=True,
    )
    apply_price = fields.Boolean(
        string="Apply Price update",
        default=False,
    )
    new_price = fields.Float(
        string="New Price",
    )

    apply_discount = fields.Boolean(
        string="Apply Discount update",
        default=False,
    )
    new_discount = fields.Float(
        string="New Discount %",
    )

    apply_partner_id = fields.Boolean(
        string="Apply Customer",
        default=False,
    )
    new_partner_id = fields.Many2one(
        string="Customer",
        comodel_name="res.partner",
    )

    apply_pricelist_id = fields.Boolean(
        string="Apply Pricelist",
        default=False,
    )
    new_pricelist_id = fields.Many2one(
        string="Pricelist",
        comodel_name="product.pricelist",
        domain="[('is_pms_available', '=', True)]",
    )

    apply_board_service = fields.Boolean(
        string="Add Board Service to reservations",
        default=False,
    )
    new_board_service_id = fields.Many2one(
        string="New Board Service",
        comodel_name="pms.board.service",
    )

    apply_service = fields.Boolean(
        string="Add Service to reservations",
        default=False,
    )
    new_service_id = fields.Many2one(
        string="New Service",
        comodel_name="product.product",
        domain="[('sale_ok','=',True)]",
    )

    apply_day_qty = fields.Boolean(
        string="Change cuantity service per day",
        help="If not set, it will use the default product day qty",
        default=False,
    )
    day_qty = fields.Integer(
        string="Quantity per day",
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

    def _default_folio_id(self):
        folio_id = self._context.get("active_id")
        folio = self.env["pms.folio"].browse(folio_id)
        return folio

    def _default_reservation_ids(self):
        folio_id = self._context.get("active_id")
        folio = self.env["pms.folio"].browse(folio_id)
        return folio.reservation_ids

    def _default_room_type_filter_ids(self):
        folio_id = self._context.get("active_id")
        folio = self.env["pms.folio"].browse(folio_id)
        return self.env["pms.room.type"].browse(
            folio.mapped("reservation_ids.room_type_id.id")
        )

    def default_change_new_checkin(self):
        folio_id = self._context.get("active_id")
        folio = self.env["pms.folio"].browse(folio_id)
        return min(folio.reservation_ids.mapped("checkin"), default=False)

    def default_change_new_checkout(self):
        folio_id = self._context.get("active_id")
        folio = self.env["pms.folio"].browse(folio_id)
        return max(folio.reservation_ids.mapped("checkout"), default=False)

    def _default_service_ids(self):
        folio_id = self._context.get("active_id")
        folio = self.env["pms.folio"].browse(folio_id)
        return folio.service_ids

    def default_change_from_date(self):
        folio_id = self._context.get("active_id")
        folio = self.env["pms.folio"].browse(folio_id)
        return min(folio.reservation_ids.mapped("checkin"), default=False)

    def default_change_to_date(self):
        folio_id = self._context.get("active_id")
        folio = self.env["pms.folio"].browse(folio_id)
        return max(folio.reservation_ids.mapped("checkout"), default=False)

    @api.depends("new_checkin", "new_checkout")
    def _compute_nights(self):
        for record in self:
            record.nights = (record.new_checkout - record.new_checkin).days

    @api.depends("reservation_ids")
    def _compute_dates_incongruence(self):
        self.dates_incongruence = False
        for record in self:
            if (
                len(set(record.reservation_ids.mapped("checkin"))) > 1
                or len(set(record.reservation_ids.mapped("checkout"))) > 1
            ):
                record.dates_incongruence = True

    @api.depends("folio_id")
    def _compute_allowed_reservation_ids(self):
        self.ensure_one()
        self.allowed_reservation_ids = self.folio_id.reservation_ids

    @api.depends("folio_id")
    def _compute_allowed_service_ids(self):
        self.ensure_one()
        self.allowed_service_ids = self.folio_id.service_ids

    @api.depends("folio_id")
    def _compute_allowed_room_type_ids(self):
        self.ensure_one()
        self.allowed_room_type_ids = self.env["pms.room.type"].browse(
            self.folio_id.mapped("reservation_ids.room_type_id.id")
        )

    @api.onchange("room_type_filter_ids")
    def _onchange_room_type_filter_ids(self):
        self.service_ids = self.folio_id.service_ids.filtered(
            lambda s: s.reservation_id
            and s.reservation_id.room_type_id.id in self.room_type_filter_ids.ids
        )
        self.reservation_ids = self.folio_id.reservation_ids.filtered(
            lambda r: r.room_type_id.id in self.room_type_filter_ids.ids
        )

    @api.onchange("reservation_ids")
    def _onchange_reservations_ids(self):
        self.new_checkin = min(self.reservation_ids.mapped("checkin"), default=False)
        self.new_checkout = max(self.reservation_ids.mapped("checkout"), default=False)

    def button_change(self):
        week_days_to_apply = (
            self.apply_on_monday,
            self.apply_on_tuesday,
            self.apply_on_wednesday,
            self.apply_on_thursday,
            self.apply_on_friday,
            self.apply_on_saturday,
            self.apply_on_sunday,
        )
        if self.modification_type == "dates":
            self._update_dates(
                reservations=self.reservation_ids,
                new_checkin=self.new_checkin,
                new_checkout=self.new_checkout,
            )
        else:
            dates = [
                self.change_from_date + timedelta(days=d)
                for d in range((self.change_to_date - self.change_from_date).days + 1)
            ]
            if self.modification_type == "reservations":
                reservation_lines = self.reservation_ids.reservation_line_ids
                if not self.apply_on_all_week:
                    reservation_lines = reservation_lines.filtered(
                        lambda x: week_days_to_apply[x.date.timetuple()[6]]
                        and x.date in dates
                    )
                if self.apply_discount or self.apply_price:
                    self._update_reservations(
                        reservation_lines=reservation_lines,
                        new_price=self.apply_price and self.new_price,
                        new_discount=self.apply_discount and self.new_discount,
                    )
                if self.apply_board_service and self.new_board_service_id:
                    self._add_board_service(
                        reservations=self.reservation_ids,
                        new_board_service_id=self.new_board_service_id.id,
                    )
                if self.apply_service and self.new_service_id:
                    self._add_service(
                        reservations=self.reservation_ids,
                        new_service_id=self.new_service_id.id,
                        day_qty=self.day_qty if self.apply_day_qty else -1,
                    )
                if self.apply_pricelist_id and self.new_pricelist_id:
                    self.reservation_ids.pricelist_id = self.new_pricelist_id
                    self.folio_id.pricelist_id = self.new_pricelist_id
                if self.apply_partner_id and self.new_partner_id:
                    self.reservation_ids.partner_id = self.new_partner_id
                    if not self.folio_id.partner_id:
                        self.folio_id.partner_id = self.new_partner_id
            elif self.modification_type == "services":
                service_lines = self.service_ids.service_line_ids
                if not self.apply_on_all_week:
                    reservation_lines = service_lines.filtered(
                        lambda x: week_days_to_apply[x.date.timetuple()[6]]
                        and x.date in dates
                    )
                self._update_services(
                    service_lines=service_lines,
                    new_price=self.apply_price and self.new_price,
                    new_discount=self.apply_discount and self.new_discount,
                )

    def _update_dates(self, reservations, new_checkin, new_checkout):
        for res in reservations:
            if new_checkin:
                res.checkin = new_checkin
            if new_checkout:
                res.checkout = new_checkout

    def _update_reservations(
        self, reservation_lines, new_price=False, new_discount=False
    ):
        line_vals = {}
        if new_price:
            line_vals["price"] = new_price
        if new_discount:
            line_vals["discount"] = new_discount
        if line_vals:
            reservation_lines.write(line_vals)

    def _add_board_service(self, reservations, new_board_service_id):
        for reservation in reservations:
            if new_board_service_id in reservation.room_type_id.mapped(
                "board_service_room_type_ids.pms_board_service_id.id"
            ):
                reservation.board_service_room_id = (
                    reservation.room_type_id.board_service_room_type_ids.filtered(
                        lambda x: x.pms_board_service_id.id == new_board_service_id
                        and (
                            reservation.folio_id.pms_property_id.id
                            in x.pms_property_ids.ids
                            or not x.pms_property_ids
                        )
                    )
                )

    def _add_service(self, reservations, new_service_id, day_qty):
        old_services = reservations.service_ids
        reservations.write(
            {
                "service_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": new_service_id,
                        },
                    )
                ]
            }
        )
        new_services = reservations.service_ids - old_services
        # Use -1 to set default qty qty per day
        if day_qty > -1:
            new_services.day_qty = day_qty

    def _update_services(
        self, service_lines, new_price=False, new_discount=False, new_day_qty=False
    ):
        line_vals = {}
        if new_price:
            line_vals["price_unit"] = new_price
        if new_discount:
            line_vals["discount"] = new_discount
        if new_day_qty:
            line_vals["day_qty"] = new_day_qty
        if line_vals:
            service_lines.write(line_vals)
