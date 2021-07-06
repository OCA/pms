import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ReservationSplitJoinSwapWizard(models.TransientModel):
    _name = "pms.reservation.split.join.swap.wizard"
    _description = "Operations in reservations"

    operation = fields.Selection(
        string="Operation",
        help="Operation to be applied on the reservation",
        selection=[
            ("swap", "Swap rooms"),
            ("split", "Split reservation"),
            ("join", "Join reservation"),
        ],
        default=lambda self: self._context.get("default_operation")
        if self._context.get("default_operation")
        else "swap",
    )
    reservation_id = fields.Many2one(
        string="Reservation",
        default=lambda self: self.env["pms.reservation"]
        .browse(self._context.get("active_id"))
        .id
        if self._context.get("active_id")
        else False,
        comodel_name="pms.reservation",
    )
    checkin = fields.Date(
        string="Check In",
        help="Checkin in reservation",
        default=lambda self: self.env["pms.reservation"]
        .browse(self._context.get("active_id"))
        .checkin
        if self._context.get("active_id")
        else False,
    )
    checkout = fields.Date(
        string="Check Out",
        help="checkout in reservation",
        default=lambda self: self.env["pms.reservation"]
        .browse(self._context.get("active_id"))
        .checkout
        if self._context.get("active_id")
        else False,
    )
    reservation_ids = fields.Many2many(
        string="Reservations",
        readonly=False,
        store=True,
        comodel_name="pms.reservation",
        compute="_compute_reservations",
    )
    room_source = fields.Many2one(
        string="Room Source",
        default=lambda self: self.env["pms.reservation"]
        .browse(self._context.get("active_id"))
        .preferred_room_id
        if self._context.get("active_id")
        and not self.env["pms.reservation"]
        .browse(self._context.get("active_id"))
        .splitted
        else False,
        comodel_name="pms.room",
        domain="[('id', 'in', allowed_rooms_sources)]",
    )
    room_target = fields.Many2one(
        string="Room Target",
        comodel_name="pms.room",
        domain="[('id', 'in', allowed_rooms_target)]",
    )
    allowed_rooms_sources = fields.Many2many(
        string="Allowed rooms source",
        store=True,
        readonly=False,
        comodel_name="pms.room",
        relation="pms_wizard_split_join_swap_reservation_rooms_source",
        column1="wizard_id",
        column2="room_id",
        compute="_compute_allowed_rooms_source",
    )
    allowed_rooms_target = fields.Many2many(
        string="Allowed rooms target",
        comodel_name="pms.room",
        store=True,
        readonly=False,
        relation="pms_wizard_split_join_swap_reservation_rooms_target",
        column1="wizard_id",
        column2="room_id",
        compute="_compute_allowed_rooms_target",
    )
    reservation_lines_to_change = fields.One2many(
        string="Reservations Lines To Change",
        comodel_name="pms.wizard.reservation.lines.split",
        inverse_name="reservation_wizard_id",
        compute="_compute_reservation_lines",
        store=True,
        readonly=False,
    )

    @api.depends("checkin", "checkout", "room_source", "room_target")
    def _compute_reservation_ids(self):
        for record in self:
            if record.checkin and record.checkout:
                reservation_ids = list()
                for date_iterator in [
                    record.checkin + datetime.timedelta(days=x)
                    for x in range(0, (record.checkout - record.checkin).days)
                ]:
                    domain_lines = []
                    if record.room_source and record.room_target:
                        domain_lines.extend(
                            [
                                "|",
                                ("room_id", "=", record.room_source.id),
                                ("room_id", "=", record.room_target.id),
                            ]
                        )

                    domain_lines.append(("date", "=", date_iterator))
                    lines = self.env["pms.reservation.line"].search(domain_lines)
                    reservation_ids.extend(lines.mapped("reservation_id.id"))
                reservations = (
                    self.env["pms.reservation"]
                    .search(
                        [
                            ("id", "in", reservation_ids),
                            ("rooms", "!=", False),
                        ]
                    )
                    .sorted("rooms")
                )
                record.reservation_ids = reservations
            else:
                record.reservation_ids = False

    @api.depends("reservation_id")
    def _compute_reservation_lines(self):
        for record in self:
            if record.reservation_id:
                cmds = [(5, 0, 0)]
                for line in record.reservation_id.reservation_line_ids:
                    cmds.append(
                        (
                            0,
                            0,
                            {
                                "reservation_wizard_id": record.id,
                                "room_id": line.room_id,
                                "date": line.date,
                            },
                        )
                    )
                    record.reservation_lines_to_change = cmds
            else:
                record.reservation_lines_to_change = False

    @api.depends("checkin", "checkout")
    def _compute_allowed_rooms_source(self):
        for record in self:
            record.allowed_rooms_sources = (
                record.reservation_ids.reservation_line_ids.mapped("room_id")
            )

    @api.depends_context("default_operation")
    @api.depends("checkin", "checkout", "room_source", "operation")
    def _compute_allowed_rooms_target(self):
        for record in self:
            record.allowed_rooms_target = False
            record.room_target = False
            if record.checkin and record.checkout:
                pms_property = record.reservation_id.pms_property_id
                pms_property = pms_property.with_context(
                    checkin=record.checkin,
                    checkout=record.checkout,
                    room_type_id=False,  # Allows to choose any available room
                    current_lines=record.reservation_id.reservation_line_ids.ids,
                    pricelist_id=record.reservation_id.pricelist_id.id,
                )
                rooms_available = pms_property.free_room_ids

                domain = [("capacity", ">=", record.reservation_id.adults)]
                if record.room_source:
                    domain.append(("id", "!=", record.room_source.id))

                if record.operation == "swap":
                    domain.append(
                        (
                            "id",
                            "in",
                            record.reservation_ids.reservation_line_ids.mapped(
                                "room_id"
                            ).ids,
                        )
                    )
                else:
                    domain.extend(
                        [
                            ("id", "in", rooms_available.ids),
                        ]
                    )
                rooms = self.env["pms.room"].search(domain)
                record.allowed_rooms_target = rooms

    @api.model
    def reservation_split(self, reservation, date, room):
        if not reservation:
            raise UserError(_("Invalid reservation"))
        if not reservation or not reservation.reservation_line_ids.filtered(
            lambda x: x.date == date
        ):
            raise UserError(_("Invalid date for reservation line "))

        if not self.browse(room.id):
            raise UserError(_("The room does not exist"))
        pms_property = reservation.pms_property_id.with_context(
            checkin=date,
            checkout=(
                datetime.datetime(year=date.year, month=date.month, day=date.day)
                + datetime.timedelta(days=1)
            ).date(),
            current_lines=reservation.reservation_line_ids.ids,
            pricelist_id=reservation.pricelist_id.id,
        )
        rooms_available = pms_property.free_room_ids

        if room not in rooms_available:
            raise UserError(_("The room is not available"))

        reservation.reservation_line_ids.filtered(
            lambda x: x.date == date
        ).room_id = room.id

    @api.model
    def reservation_join(self, reservation, room):
        pms_property = reservation.pms_property_id
        pms_property = pms_property.with_context(
            checkin=reservation.checkin,
            checkout=reservation.checkout,
            current_lines=reservation.reservation_line_ids.ids,
            pricelist_id=reservation.pricelist_id.id,
        )
        rooms_available = pms_property.free_room_ids

        if room in rooms_available:
            for line in (
                self.env["pms.reservation"]
                .search([("id", "=", reservation.id)])
                .reservation_line_ids
            ):
                line.room_id = room.id
        else:
            raise UserError(_("Room {} not available.".format(room.name)))

    @api.model
    def reservations_swap(self, checkin, checkout, source, target):
        reservations = self.env["pms.reservation"].search(
            [("checkin", ">=", checkin), ("checkout", "<=", checkout)]
        )
        lines = self.env["pms.reservation.line"].search_count(
            [("room_id", "=", source), ("reservation_id", "in", reservations.ids)]
        )
        if not lines:
            raise UserError(_("There's no reservations lines with provided room"))

        for date_iterator in [
            checkin + datetime.timedelta(days=x)
            for x in range(0, (checkout - checkin).days)
        ]:
            line_room_source = self.env["pms.reservation.line"].search(
                [("date", "=", date_iterator), ("room_id", "=", source)]
            )
            line_room_target = self.env["pms.reservation.line"].search(
                [("date", "=", date_iterator), ("room_id", "=", target)]
            )
            if line_room_source and line_room_target:

                # this causes an unique error constraint
                line_room_target.occupies_availability = False
                line_room_source.occupies_availability = False

                line_room_target.room_id = source
                line_room_source.room_id = target

                self.flush()

                line_room_target._compute_occupies_availability()
                line_room_source._compute_occupies_availability()

            else:
                line_room_source.room_id = target

    def action_split(self):
        for record in self:
            for line in record.reservation_lines_to_change:
                self.reservation_split(
                    record.reservation_id,
                    line.date,
                    line.room_id,
                )

    def action_join(self):
        for record in self:
            self.reservation_join(record.reservation_id, record.room_target)

    def action_swap(self):
        self.reservations_swap(
            self.checkin, self.checkout, self.room_source.id, self.room_target.id
        )


class ReservationLinesToSplit(models.TransientModel):
    _name = "pms.wizard.reservation.lines.split"
    _description = "Lines available to split"

    reservation_wizard_id = fields.Many2one(
        string="Reservation Wizard",
        comodel_name="pms.reservation.split.join.swap.wizard",
    )
    date = fields.Date(
        string="Date",
    )
    room_id = fields.Many2one(
        string="Room",
        comodel_name="pms.room",
        domain="[('id', 'in', allowed_room_ids)]",
    )
    allowed_room_ids = fields.Many2many(
        string="Allowed Rooms",
        help="It contains all available rooms for this line",
        store=True,
        comodel_name="pms.room",
        compute="_compute_allowed_room_ids",
        # readonly=False
    )

    @api.depends(
        "date",
        "room_id",
        "reservation_wizard_id.reservation_id.pricelist_id",
    )
    def _compute_allowed_room_ids(self):
        for line in self:
            reservation = line.reservation_wizard_id.reservation_id
            rooms_available = False
            if line.date and reservation:
                if reservation.overbooking or reservation.state in ("cancel"):
                    line.allowed_room_ids = self.env["pms.room"].search(
                        [("active", "=", True)]
                    )
                    return
                pms_property = reservation.pms_property_id
                pms_property = pms_property.with_context(
                    checkin=line.date,
                    checkout=line.date + datetime.timedelta(days=1),
                    room_type_id=False,  # Allows to choose any available room
                    pricelist_id=reservation.pricelist_id.id,
                )
                rooms_available = pms_property.free_room_ids
                rooms_available += line.room_id
                line.allowed_room_ids = rooms_available
            else:
                line.allowed_room_ids = False
