from odoo import _, api, fields, models


class WizardFolioChanges(models.TransientModel):

    _name = "wizard.folio.changes"
    _description = "Folio Changes"

    def _default_folio_id(self):
        folio_id = self._context.get("active_id")
        folio = self.env["pms.folio"].browse(folio_id)
        return folio

    def _default_reservation_ids(self):
        folio_id = self._context.get("active_id")
        folio = self.env["pms.folio"].browse(folio_id)
        return folio.reservation_ids

    folio_id = fields.Many2one(
        "pms.folio",
        string="Folio",
        default=_default_folio_id,
    )
    reservation_ids = fields.Many2many(
        "pms.reservation",
        string="Reservations",
        default=_default_reservation_ids,
        domain="[('id', 'in', allowed_reservation_ids)]",
    )
    allowed_reservation_ids = fields.Many2many(
        "pms.reservation",
        string="Allowed Reservations",
        compute="_compute_allowed_reservations",
    )
    new_price = fields.Float(
        string="New Price",
    )
    new_discount = fields.Float(
        string="New Discount %",
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
