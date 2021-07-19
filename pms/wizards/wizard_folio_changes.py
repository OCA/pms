from odoo import _, api, fields, models


class WizardFolioChanges(models.TransientModel):

    _name = "wizard.folio.changes"
    _description = "Folio Changes"

    folio_id = fields.Many2one(
        string="Folio",
        default=lambda self: self._default_folio_id(),
        comodel_name="pms.folio",
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
        compute="_compute_allowed_reservations",
    )
    new_price = fields.Float(
        string="New Price",
    )
    new_discount = fields.Float(
        string="New Discount %",
    )
    new_board_service_id = fields.Many2one(
        string="New Board Service",
        comodel_name="pms.board.service",
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

    @api.depends("folio_id")
    def _compute_allowed_reservations(self):
        self.ensure_one()
        self.allowed_reservation_ids = self.folio_id.reservation_ids

    def button_change(self):
        vals = {}
        week_days_to_apply = (
            self.apply_on_monday,
            self.apply_on_tuesday,
            self.apply_on_wednesday,
            self.apply_on_thursday,
            self.apply_on_friday,
            self.apply_on_saturday,
            self.apply_on_sunday,
        )
        reservation_lines = self.reservation_ids.reservation_line_ids
        if not self.apply_on_all_week:
            reservation_lines = reservation_lines.filtered(
                lambda x: week_days_to_apply[x.date.timetuple()[6]]
            )
        if self.new_price or self.new_discount:
            if self.new_price:
                vals["price"] = self.new_price
            if self.new_discount:
                vals["discount"] = self.new_discount

            reservation_lines.write(vals)

            self.folio_id.message_post(
                body=_(
                    "Prices/Discounts have been changed from folio",
                )
            )
            reservations = self.env["pms.reservation"].browse(
                reservation_lines.mapped("reservation_id.id")
            )
            for reservation in reservations:
                reservation.message_post(
                    body=_(
                        "Prices/Discounts have been changed from folio",
                    )
                )
        if self.new_board_service_id:
            for reservation in self.reservation_ids:
                if (
                    self.new_board_service_id.id
                    in reservation.room_type_id.board_service_room_type_ids.ids
                ):
                    reservation.board_service_room_id = (
                        reservation.room_type_id.board_service_room_type_ids.filtered(
                            lambda x: x.pms_board_service_id.id
                            == self.new_board_service_id.id
                            and (
                                self.folio_id.pms_property_id.id
                                in x.pms_property_ids.ids
                                or not x.pms_property_ids
                            )
                        )
                    )
                    reservation.message_post(
                        body=_(
                            "Board service has been changed from folio",
                        )
                    )
