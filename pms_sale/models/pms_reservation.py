# Copyright (c) 2021 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime, timedelta

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

AVAILABLE_PRIORITIES = [("0", "Normal"), ("1", "Low"), ("2", "High"), ("3", "Urgent")]


class PmsReservation(models.Model):
    _name = "pms.reservation"
    _description = "Reservation"
    _order = "start, id"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    def _default_stage_id(self):
        return self.env.ref("pms_sale.pms_stage_new", raise_if_not_found=False)

    def _get_duration(self, start, stop):
        """ Get the duration value between the 2 given dates. """
        if not start or not stop:
            return 0
        duration = (stop - start).total_seconds() / (24 * 3600)
        return round(duration, 0)

    @api.depends("guest_ids")
    def _compute_no_of_guests(self):
        self.no_of_guests = 0
        if self.guest_ids:
            self.no_of_guests = len(self.guest_ids)

    name = fields.Char(
        string="Reservation #",
        help="Reservation Number",
        required=True,
        readonly=True,
        index=True,
        copy=False,
        default=lambda self: _("New"),
    )
    start = fields.Datetime(
        "Checkin",
        required=True,
        tracking=True,
        default=fields.Date.today,
        help="Start date of the reservation",
    )
    stop = fields.Datetime(
        "Checkout",
        required=True,
        tracking=True,
        default=fields.Date.today,
        compute="_compute_stop",
        readonly=False,
        store=True,
        help="Stop date of the reservation",
    )
    duration = fields.Integer(
        "Nights", compute="_compute_duration", store=True, readonly=False
    )
    date = fields.Datetime(string="Date", default=lambda self: fields.Datetime.now())
    stage_id = fields.Many2one(
        "pms.stage",
        string="Stage",
        store=True,
        tracking=True,
        index=True,
        default=_default_stage_id,
        group_expand="_read_group_stage_ids",
    )
    team_id = fields.Many2one(
        "pms.team", string="Team", related="property_id.team_id", store=True
    )
    property_id = fields.Many2one("pms.property", string="Property")
    sale_order_id = fields.Many2one("sale.order", string="Sales Order")
    sale_order_line_id = fields.Many2one("sale.order.line", string="Sales Order Line")
    invoice_status = fields.Selection(
        related="sale_order_id.invoice_status", store=True, index=True
    )
    partner_id = fields.Many2one("res.partner", string="Booked by")
    user_id = fields.Many2one(
        "res.users", string="Responsible", default=lambda self: self.env.user.id
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company.id,
    )
    adults = fields.Integer(string="Adults")
    children = fields.Integer(string="Children")
    no_of_guests = fields.Integer(
        "Number of Guests", compute="_compute_no_of_guests", store=True
    )
    guest_ids = fields.One2many(
        "pms.reservation.guest", "reservation_id", string="Guests"
    )
    priority = fields.Selection(
        AVAILABLE_PRIORITIES,
        string="Priority",
        index=True,
        default=AVAILABLE_PRIORITIES[0][0],
    )
    tag_ids = fields.Many2many("pms.tag", string="Tags")
    color = fields.Integer("Color Index", default=0)
    invoice_count = fields.Integer(
        string="Invoice Count",
        compute="_compute_invoice_count",
        readonly=True,
        copy=False,
    )

    @api.depends("stop", "start")
    def _compute_duration(self):
        for reservation in self.with_context(dont_notify=True):
            reservation.duration = self._get_duration(
                reservation.start, reservation.stop
            )

    @api.depends("start", "duration")
    def _compute_stop(self):
        # stop and duration fields both depends on the start field.
        # But they also depends on each other.
        # When start is updated, we want to update the stop datetime based on
        # the *current* duration.
        # In other words, we want: change start => keep the duration fixed and
        # recompute stop accordingly.
        # However, while computing stop, duration is marked to be recomputed.
        # Calling `reservation.duration` would trigger its recomputation.
        # To avoid this we manually mark the field as computed.
        duration_field = self._fields["duration"]
        self.env.remove_to_compute(duration_field, self)
        for reservation in self:
            reservation.stop = reservation.start + timedelta(days=reservation.duration)

    def _compute_invoice_count(self):
        for reservation in self:
            invoices = (
                self.env["account.move.line"]
                .search([("pms_reservation_id", "=", reservation.id)])
                .mapped("move_id")
                .filtered(lambda r: r.move_type in ("out_invoice", "out_refund"))
            )
            reservation.invoice_count = len(invoices)

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        search_domain = [("stage_type", "=", "reservation")]
        if self.env.context.get("default_team_id"):
            search_domain = [
                "&",
                ("team_ids", "in", self.env.context["default_team_id"]),
            ] + search_domain
        return stages.search(search_domain, order=order)

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code("pms.reservation") or _(
                "New"
            )
        return super().create(vals)

    @api.onchange("property_id")
    def onchange_property_id(self):
        user_tz = self.env.user.tz or "UTC"
        utc = pytz.timezone("UTC")
        timezone = pytz.timezone(user_tz)
        if (
            self.property_id
            and self.start
            and self.stop
            and self.property_id.checkin
            and self.property_id.checkout
        ):
            start_datetime = (
                str(self.start.date())
                + " "
                + str(timedelta(hours=self.property_id.checkin))
            )
            with_timezone = timezone.localize(
                datetime.strptime(start_datetime, DEFAULT_SERVER_DATETIME_FORMAT)
            )
            start_datetime = with_timezone.astimezone(utc)
            self.start = start_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            end_datetime = (
                str(self.stop.date())
                + " "
                + str(timedelta(hours=self.property_id.checkout))
            )
            with_timezone = timezone.localize(
                datetime.strptime(end_datetime, DEFAULT_SERVER_DATETIME_FORMAT)
            )
            end_datetime = with_timezone.astimezone(utc)
            self.stop = end_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        else:
            self.start = self.start.date()
            self.stop = self.stop.date()

    @api.constrains("property_id", "no_of_guests")
    def _check_max_no_of_guests(self):
        for reservation in self:
            if reservation.no_of_guests > reservation.property_id.no_of_guests:
                raise ValidationError(
                    _(
                        """Too many guests (%s) on the reservation: the property
                         accepts a maximum of %s guests."""
                        % (
                            reservation.no_of_guests,
                            reservation.property_id.no_of_guests,
                        )
                    )
                )

    @api.constrains("property_id", "stage_id", "start", "stop")
    def _check_no_of_reservations(self):
        stage_ids = [
            self.env.ref("pms_sale.pms_stage_new", raise_if_not_found=False).id,
            self.env.ref("pms_sale.pms_stage_cancelled", raise_if_not_found=False).id,
        ]
        for rec in self:
            if rec.stage_id.id not in stage_ids:
                reservation = self.search(
                    [
                        ("property_id", "=", rec.property_id.id),
                        ("stage_id", "not in", stage_ids),
                        ("id", "!=", rec.id),
                        ("start", "<=", rec.stop),
                        ("stop", ">=", rec.start),
                    ]
                )
                if reservation:
                    raise ValidationError(
                        _(
                            "You cannot have 2 reservations on the same night at the "
                            "same property."
                        )
                    )

    @api.constrains("property_id.min_nights", "property_id.max_nights", "duration")
    def _check_no_of_nights(self):
        for rec in self:
            if (
                rec.duration > rec.property_id.min_nights
                and rec.property_id.max_nights < rec.duration
            ):
                raise ValidationError(
                    _(
                        "The number of nights must be between %s and %s."
                        % (
                            rec.property_id.min_nights,
                            rec.property_id.max_nights,
                        )
                    )
                )

    def action_book(self):
        return self.write(
            {
                "stage_id": self.env.ref(
                    "pms_sale.pms_stage_booked", raise_if_not_found=False
                ).id,
            }
        )

    def action_confirm(self):
        return self.write(
            {
                "stage_id": self.env.ref(
                    "pms_sale.pms_stage_confirmed", raise_if_not_found=False
                ).id
            }
        )

    def action_check_in(self):
        return self.write(
            {
                "stage_id": self.env.ref(
                    "pms_sale.pms_stage_checked_in", raise_if_not_found=False
                ).id,
                "start": fields.Datetime.now(),
            }
        )

    def action_check_out(self):
        return self.write(
            {
                "stage_id": self.env.ref(
                    "pms_sale.pms_stage_checked_out", raise_if_not_found=False
                ).id,
                "stop": fields.Datetime.now(),
            }
        )

    def action_cancel(self):
        self.write(
            {
                "stage_id": self.env.ref(
                    "pms_sale.pms_stage_cancelled", raise_if_not_found=False
                ).id
            }
        )

    def action_view_invoices(self):
        for reservation in self:
            action = self.env.ref("account.action_move_out_invoice_type").read()[0]
            invoices = (
                self.env["account.move.line"]
                .search([("pms_reservation_id", "=", reservation.id)])
                .mapped("move_id")
                .filtered(lambda r: r.move_type in ("out_invoice", "out_refund"))
            )
            action["domain"] = [("id", "in", invoices.ids)]
            return action

    @api.model
    def get_selections(self):
        cities = list(
            {rec.city for rec in self.env["pms.property"].search([]) if rec.city}
        )
        cities.sort()
        values = {"city": cities}
        return values
