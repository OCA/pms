# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import logging
import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PmsReservation(models.Model):
    _name = "pms.reservation"
    _description = "Reservation"
    _inherit = ["mail.thread", "mail.activity.mixin", "portal.mixin"]
    _order = "priority asc, create_date desc, write_date desc"
    # TODO:
    #  consider near_to_checkin & pending_notifications to order
    _check_pms_properties_auto = True
    _check_company_auto = True

    name = fields.Text(
        string="Reservation Id",
        help="Reservation Name",
        readonly=True,
    )
    priority = fields.Integer(
        string="Priority",
        help="Priority of a reservation",
        index=True,
        store="True",
        compute="_compute_priority",
    )
    preferred_room_id = fields.Many2one(
        string="Room",
        help="It's the preferred room assigned to reservation, "
        "empty if reservation is splitted",
        copy=False,
        comodel_name="pms.room",
        ondelete="restrict",
        domain="["
        "('id', 'in', allowed_room_ids),"
        "('pms_property_id', '=', pms_property_id),"
        "]",
        tracking=True,
        check_pms_properties=True,
    )
    allowed_room_ids = fields.Many2many(
        string="Allowed Rooms",
        help="It contains all available rooms for this reservation",
        comodel_name="pms.room",
        compute="_compute_allowed_room_ids",
    )
    folio_id = fields.Many2one(
        string="Folio",
        help="The folio where the reservations are included",
        copy=False,
        comodel_name="pms.folio",
        ondelete="restrict",
        tracking=True,
        check_company=True,
    )
    sale_line_ids = fields.One2many(
        comodel_name="folio.sale.line",
        inverse_name="reservation_id",
        string="Sale Lines",
        copy=False,
    )
    board_service_room_id = fields.Many2one(
        string="Board Service",
        help="Board Service included in the room",
        readonly=False,
        store=True,
        comodel_name="pms.board.service.room.type",
        compute="_compute_board_service_room_id",
        tracking=True,
        check_pms_properties=True,
    )
    room_type_id = fields.Many2one(
        string="Room Type",
        help="Room Type sold on the reservation,"
        "it doesn't necessarily correspond to"
        " the room actually assigned",
        readonly=False,
        copy=False,
        store=True,
        comodel_name="pms.room.type",
        ondelete="restrict",
        compute="_compute_room_type_id",
        tracking=True,
        check_pms_properties=True,
    )
    partner_id = fields.Many2one(
        string="Customer",
        help="Name of who made the reservation",
        readonly=False,
        store=True,
        comodel_name="res.partner",
        ondelete="restrict",
        compute="_compute_partner_id",
        tracking=True,
        check_pms_properties=True,
    )
    agency_id = fields.Many2one(
        string="Agency",
        help="Agency that made the reservation",
        readonly=False,
        store=True,
        related="folio_id.agency_id",
        depends=["folio_id.agency_id"],
        tracking=True,
    )
    channel_type_id = fields.Many2one(
        string="Channel Type",
        help="Sales Channel through which the reservation was managed",
        readonly=False,
        store=True,
        related="folio_id.channel_type_id",
        tracking=True,
    )
    closure_reason_id = fields.Many2one(
        string="Closure Reason",
        help="Reason why the reservation cannot be made",
        related="folio_id.closure_reason_id",
        check_pms_properties=True,
    )
    company_id = fields.Many2one(
        string="Company",
        help="Company to which the reservation belongs",
        readonly=True,
        store=True,
        related="folio_id.company_id",
    )
    pms_property_id = fields.Many2one(
        string="Pms Property",
        help="Property to which the reservation belongs",
        store=True,
        readonly=False,
        default=lambda self: self.env.user.get_active_property_ids()[0],
        related="folio_id.pms_property_id",
        comodel_name="pms.property",
        check_pms_properties=True,
    )
    reservation_line_ids = fields.One2many(
        string="Reservation Lines",
        help="They are the lines of the reservation into a reservation,"
        "they corresponds to the nights",
        readonly=False,
        copy=False,
        store=True,
        compute="_compute_reservation_line_ids",
        comodel_name="pms.reservation.line",
        inverse_name="reservation_id",
        check_pms_properties=True,
    )
    service_ids = fields.One2many(
        string="Services",
        help="Included services in the reservation",
        readonly=False,
        store=True,
        comodel_name="pms.service",
        inverse_name="reservation_id",
        compute="_compute_service_ids",
        check_company=True,
        check_pms_properties=True,
    )
    pricelist_id = fields.Many2one(
        string="Pricelist",
        help="Pricelist that guides the prices of the reservation",
        readonly=False,
        store=True,
        comodel_name="product.pricelist",
        ondelete="restrict",
        compute="_compute_pricelist_id",
        tracking=True,
        check_pms_properties=True,
    )
    user_id = fields.Many2one(
        string="Salesperson",
        help="User who manages the reservation",
        readonly=False,
        store=True,
        related="folio_id.user_id",
        depends=["folio_id.user_id"],
        default=lambda self: self.env.user.id,
    )
    show_update_pricelist = fields.Boolean(
        string="Has Pricelist Changed",
        help="Technical Field, True if the pricelist was changed;\n"
        " this will then display a recomputation button",
        store=True,
        compute="_compute_show_update_pricelist",
    )
    commission_percent = fields.Float(
        string="Commission percent (%)",
        help="Percentage corresponding to commission",
        readonly=False,
        store=True,
        compute="_compute_commission_percent",
        tracking=True,
    )
    commission_amount = fields.Float(
        string="Commission amount",
        help="Amount corresponding to commission",
        store=True,
        compute="_compute_commission_amount",
    )
    checkin_partner_ids = fields.One2many(
        string="Checkin Partners",
        help="Guests who will occupy the room",
        readonly=False,
        copy=False,
        store=True,
        compute="_compute_checkin_partner_ids",
        comodel_name="pms.checkin.partner",
        inverse_name="reservation_id",
        check_pms_properties=True,
    )
    count_pending_arrival = fields.Integer(
        string="Pending Arrival",
        help="Number of guest with pending checkin",
        store=True,
        compute="_compute_count_pending_arrival",
    )
    checkins_ratio = fields.Integer(
        string="Pending Arrival Ratio",
        help="Proportion of guest pending checkin",
        compute="_compute_checkins_ratio",
    )
    pending_checkin_data = fields.Integer(
        string="Checkin Data",
        help="Data missing at checkin",
        store=True,
        compute="_compute_pending_checkin_data",
    )
    ratio_checkin_data = fields.Integer(
        string="Complete cardex",
        help="Proportion of guest data complete at checkin",
        compute="_compute_ratio_checkin_data",
    )
    ready_for_checkin = fields.Boolean(
        string="Ready for checkin",
        help="Indicates the reservations with checkin_partner data enought to checkin",
        compute="_compute_ready_for_checkin",
    )
    allowed_checkin = fields.Boolean(
        string="Allowed checkin",
        help="Technical field, Indicates if there isn't a checkin_partner data"
        "Only can be true if checkin is today or was in the past",
        compute="_compute_allowed_checkin",
        search="_search_allowed_checkin",
    )

    allowed_checkout = fields.Boolean(
        string="Allowed checkout",
        help="Technical field, Indicates that reservation is ready for checkout"
        "only can be true if reservation state is 'onboard' or departure_delayed"
        "and checkout is today or will be in the future",
        compute="_compute_allowed_checkout",
        search="_search_allowed_checkout",
    )

    allowed_cancel = fields.Boolean(
        string="Allowed cancel",
        help="Technical field, Indicates that reservation can be cancelled,"
        "that happened when state is 'cancel', 'done', or 'departure_delayed'",
        compute="_compute_allowed_cancel",
        search="_search_allowed_cancel",
    )

    segmentation_ids = fields.Many2many(
        string="Segmentation",
        help="Segmentation tags to classify reservations",
        default=lambda self: self._get_default_segmentation(),
        comodel_name="res.partner.category",
        ondelete="restrict",
    )
    currency_id = fields.Many2one(
        string="Currency",
        help="The currency used in relation to the pricelist",
        readonly=True,
        store=True,
        related="pricelist_id.currency_id",
        depends=["pricelist_id"],
    )
    tax_ids = fields.Many2many(
        string="Taxes",
        help="Taxes applied in the reservation",
        readonly="False",
        store=True,
        compute="_compute_tax_ids",
        comodel_name="account.tax",
        domain=["|", ("active", "=", False), ("active", "=", True)],
    )
    adults = fields.Integer(
        string="Adults",
        help="List of adults there in guest list",
        readonly=False,
        store=True,
        compute="_compute_adults",
        tracking=True,
    )
    children_occupying = fields.Integer(
        string="Children occupying",
        help="Number of children there in guest list whose presence counts",
    )
    children = fields.Integer(
        string="Children",
        help="Number total of children there in guest list,"
        "whose presence counts or not",
        readonly=False,
        tracking=True,
    )
    to_assign = fields.Boolean(
        string="To Assign",
        help="It is True if the room of the reservation has been assigned "
        "automatically, False if it was confirmed by a person in charge",
        default=True,
    )
    state = fields.Selection(
        string="State",
        help="The state of the reservation. "
        "It can be 'Pre-reservation', 'Pending arrival', 'On Board', 'Out', "
        "'Cancelled', 'Arrival Delayed' or 'Departure Delayed'",
        readonly=True,
        index=True,
        default=lambda *a: "draft",
        copy=False,
        selection=[
            ("draft", "Pre-reservation"),
            ("confirm", "Pending arrival"),
            ("onboard", "On Board"),
            ("done", "Out"),
            ("cancel", "Cancelled"),
            ("arrival_delayed", "Arrival Delayed"),
            ("departure_delayed", "Departure delayed"),
        ],
        tracking=True,
    )
    reservation_type = fields.Selection(
        string="Reservation Type",
        help="Type of reservations. It can be 'normal', 'staff' or 'out of service",
        default=lambda *a: "normal",
        related="folio_id.reservation_type",
    )
    splitted = fields.Boolean(
        string="Splitted",
        help="Field that indicates if the reservation is split. "
        "A reservation is split when guests don't sleep in the same room every night",
        store=True,
        compute="_compute_splitted",
    )
    rooms = fields.Char(
        string="Room/s",
        help="Rooms that are reserved",
        compute="_compute_rooms",
        store=True,
        tracking=True,
    )
    credit_card_details = fields.Text(
        string="Credit Card Details", help="", related="folio_id.credit_card_details"
    )
    cancelled_reason = fields.Selection(
        string="Reason of cancellation",
        help="Field indicating type of cancellation. "
        "It can be 'late', 'intime' or 'noshow'",
        copy=False,
        compute="_compute_cancelled_reason",
        readonly=False,
        store=True,
        selection=[("late", "Late"), ("intime", "In time"), ("noshow", "No Show")],
        tracking=True,
    )
    out_service_description = fields.Text(
        string="Cause of out of service",
        help="Indicates the cause of out of service",
    )
    checkin = fields.Date(
        string="Check In",
        help="It is the checkin date of the reservation, ",
        compute="_compute_checkin",
        readonly=False,
        store=True,
        copy=False,
        tracking=True,
    )
    checkout = fields.Date(
        string="Check Out",
        help="It is the checkout date of the reservation, ",
        compute="_compute_checkout",
        readonly=False,
        store=True,
        copy=False,
        tracking=True,
    )
    arrival_hour = fields.Char(
        string="Arrival Hour",
        help="Arrival Hour (HH:MM)",
        readonly=False,
        store=True,
        compute="_compute_arrival_hour",
    )
    departure_hour = fields.Char(
        string="Departure Hour",
        help="Departure Hour (HH:MM)",
        readonly=False,
        store=True,
        compute="_compute_departure_hour",
    )
    checkin_datetime = fields.Datetime(
        string="Exact Arrival",
        help="This field is the day and time of arrival of the reservation."
        "It is formed with the checkin and arrival_hour fields",
        compute="_compute_checkin_datetime",
    )
    checkout_datetime = fields.Datetime(
        string="Exact Departure",
        help="This field is the day and time of departure of the reservation."
        "It is formed with the checkout and departure_hour fields",
        compute="_compute_checkout_datetime",
    )
    checkin_partner_count = fields.Integer(
        string="Checkin counter",
        help="Number of checkin partners in a reservation",
        compute="_compute_checkin_partner_count",
    )
    checkin_partner_pending_count = fields.Integer(
        string="Checkin Pending Num",
        help="Number of checkin partners pending to checkin in a reservation",
        compute="_compute_checkin_partner_count",
        search="_search_checkin_partner_pending",
    )
    overbooking = fields.Boolean(
        string="Is Overbooking",
        help="Indicate if exists overbooking",
        default=False,
        copy=False,
    )
    nights = fields.Integer(
        string="Nights",
        help="Number of nights of a reservation",
        compute="_compute_nights",
        store=True,
    )
    folio_pending_amount = fields.Monetary(
        string="Pending Amount",
        help="The amount that remains to be paid from folio",
        related="folio_id.pending_amount",
        tracking=True,
    )
    folio_payment_state = fields.Selection(
        string="Payment State",
        help="The status of the folio payment",
        store=True,
        related="folio_id.payment_state",
        tracking=True,
    )
    shared_folio = fields.Boolean(
        string="Shared Folio",
        help="Used to notify is the reservation folio has other reservations/services",
        compute="_compute_shared_folio",
    )
    partner_name = fields.Char(
        string="Customer Name",
        help="To whom the room is assigned",
        store=True,
        readonly=False,
        compute="_compute_partner_name",
    )
    email = fields.Char(
        string="E-mail",
        help="Customer E-mail",
        store=True,
        readonly=False,
        compute="_compute_email",
    )
    mobile = fields.Char(
        string="Mobile",
        help="Customer Mobile",
        store=True,
        readonly=False,
        compute="_compute_mobile",
    )
    partner_internal_comment = fields.Text(
        string="Internal Partner Notes",
        help="Internal notes of the partner",
        related="partner_id.comment",
        store=True,
        readonly=False,
    )
    partner_incongruences = fields.Char(
        string="partner_incongruences",
        help="indicates that some partner fields \
            on the reservation do not correspond to that of \
            the associated partner",
        compute="_compute_partner_incongruences",
    )
    partner_requests = fields.Text(
        string="Partner Requests",
        help="Guest requests",
    )
    folio_internal_comment = fields.Text(
        string="Internal Folio Notes",
        help="Internal comment for folio",
        related="folio_id.internal_comment",
        store=True,
        readonly=False,
    )
    preconfirm = fields.Boolean(
        string="Auto confirm to Save",
        help="Technical field that indicates the reservation is not comfirm yet",
        default=True,
    )
    invoice_status = fields.Selection(
        string="Invoice Status",
        help="The status of the invoices in folio. Can be 'invoiced',"
        " 'to_invoice' or 'no'.",
        store=True,
        readonly=True,
        selection=[
            ("upselling", "Upselling Opportunity"),
            ("invoiced", "Fully Invoiced"),
            ("to_invoice", "To Invoice"),
            ("no", "Nothing to Invoice"),
        ],
        compute="_compute_invoice_status",
    )
    analytic_tag_ids = fields.Many2many(
        string="Analytic Tags",
        comodel_name="account.analytic.tag",
        relation="pms_reservation_account_analytic_tag",
        column1="reservation_id",
        column2="account_analytic_tag_id",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    analytic_line_ids = fields.One2many(
        string="Analytic lines",
        comodel_name="account.analytic.line",
        inverse_name="so_line",
    )
    price_subtotal = fields.Monetary(
        string="Subtotal",
        help="Subtotal price without taxes",
        readonly=True,
        store=True,
        compute="_compute_amount_reservation",
    )
    price_total = fields.Monetary(
        string="Total",
        help="Total price with taxes",
        readonly=True,
        store=True,
        compute="_compute_amount_reservation",
        tracking=True,
    )
    price_tax = fields.Float(
        string="Taxes Amount",
        help="Total of taxes in a reservation",
        readonly=True,
        store=True,
        compute="_compute_amount_reservation",
    )
    price_services = fields.Monetary(
        string="Services Total",
        help="Total price from services of a reservation",
        readonly=True,
        store=True,
        compute="_compute_price_services",
    )
    price_room_services_set = fields.Monetary(
        string="Room Services Total",
        help="Total price of room and services",
        readonly=True,
        store=True,
        compute="_compute_price_room_services_set",
    )
    discount = fields.Float(
        string="Discount (€)",
        help="Discount of total price in reservation",
        readonly=False,
        store=True,
        digits=("Discount"),
        compute="_compute_discount",
        tracking=True,
    )

    services_discount = fields.Float(
        string="Services discount (€)",
        help="Services discount",
        readonly=False,
        store=True,
        digits=("Discount"),
        compute="_compute_services_discount",
        tracking=True,
    )
    date_order = fields.Date(
        string="Date Order",
        help="Order date of reservation",
        compute="_compute_date_order",
        store=True,
        readonly=False,
    )

    def _compute_date_order(self):
        for record in self:
            record.date_order = datetime.datetime.today()

    @api.depends(
        "checkin",
        "checkout",
        "state",
        "folio_payment_state",
        "to_assign",
    )
    def _compute_priority(self):
        # TODO: Notifications priority
        for record in self:
            if record.to_assign or record.state in (
                "arrival_delayed",
                "departure_delayed",
            ):
                record.priority = 1
            elif record.state == "cancel":
                record.priority = record.cancel_priority()
            elif record.state == "onboard":
                record.priority = record.onboard_priority()
            elif record.state in ("draf", "confirm"):
                record.priority = record.reservations_future_priority()
            elif record.state == "done":
                record.priority = record.reservations_past_priority()

    def cancel_priority(self):
        self.ensure_one()
        if self.folio_pending_amount > 0:
            return 2
        elif self.checkout >= fields.date.today():
            return 100
        else:
            return 1000 * (fields.date.today() - self.checkout).days

    def onboard_priority(self):
        self.ensure_one()
        days_for_checkout = (self.checkout - fields.date.today()).days
        if self.folio_pending_amount > 0:
            return days_for_checkout
        else:
            return 3 * days_for_checkout

    def reservations_future_priority(self):
        self.ensure_one()
        days_for_checkin = (self.checkin - fields.date.today()).days
        if days_for_checkin < 3:
            return 2 * days_for_checkin
        elif days_for_checkin < 20:
            return 3 * days_for_checkin
        else:
            return 4 * days_for_checkin

    def reservations_past_priority(self):
        self.ensure_one()
        if self.folio_pending_amount > 0:
            return 3
        days_from_checkout = (fields.date.today() - self.checkout).days
        if days_from_checkout <= 1:
            return 6
        elif days_from_checkout < 15:
            return 5 * days_from_checkout
        elif days_from_checkout <= 90:
            return 10 * days_from_checkout
        elif days_from_checkout > 90:
            return 100 * days_from_checkout

    @api.depends("pricelist_id", "room_type_id")
    def _compute_board_service_room_id(self):
        for reservation in self:
            if reservation.pricelist_id and reservation.room_type_id:
                board_service_default = self.env["pms.board.service.room.type"].search(
                    [
                        ("pms_room_type_id", "=", reservation.room_type_id.id),
                        ("by_default", "=", True),
                    ]
                )
                if (
                    not reservation.board_service_room_id
                    or not reservation.board_service_room_id.pms_room_type_id
                    == reservation.room_type_id
                ):
                    reservation.board_service_room_id = (
                        board_service_default.id if board_service_default else False
                    )
            elif not reservation.board_service_room_id:
                reservation.board_service_room_id = False

    @api.depends("preferred_room_id")
    def _compute_room_type_id(self):
        """
        This method set False to_assign when the user
        directly chooses the preferred_room_id,
        otherwise, action_assign will be used when the user manually confirms
        or changes the preferred_room_id of the reservation
        """
        for reservation in self:
            if reservation.preferred_room_id and not reservation.room_type_id:
                reservation.room_type_id = reservation.preferred_room_id.room_type_id.id
            elif not reservation.room_type_id:
                reservation.room_type_id = False

    @api.depends("checkin", "arrival_hour")
    def _compute_checkin_datetime(self):
        for reservation in self:
            checkin_hour = int(reservation.arrival_hour[0:2])
            checkin_minut = int(reservation.arrival_hour[3:5])
            checkin_time = datetime.time(checkin_hour, checkin_minut)
            checkin_datetime = datetime.datetime.combine(
                reservation.checkin, checkin_time
            )
            reservation.checkin_datetime = (
                reservation.pms_property_id.date_property_timezone(checkin_datetime)
            )

    @api.depends("checkout", "departure_hour")
    def _compute_checkout_datetime(self):
        for reservation in self:
            checkout_hour = int(reservation.departure_hour[0:2])
            checkout_minut = int(reservation.departure_hour[3:5])
            checkout_time = datetime.time(checkout_hour, checkout_minut)
            checkout_datetime = datetime.datetime.combine(
                reservation.checkout, checkout_time
            )
            reservation.checkout_datetime = (
                reservation.pms_property_id.date_property_timezone(checkout_datetime)
            )

    @api.depends(
        "reservation_line_ids.date",
        "reservation_line_ids.room_id",
        "reservation_line_ids.occupies_availability",
        "preferred_room_id",
        "pricelist_id",
        "pms_property_id",
    )
    def _compute_allowed_room_ids(self):
        for reservation in self:
            if reservation.checkin and reservation.checkout:
                if reservation.overbooking or reservation.state in ("cancel"):
                    reservation.allowed_room_ids = self.env["pms.room"].search(
                        [("active", "=", True)]
                    )
                    return
                pms_property = reservation.pms_property_id
                pms_property = pms_property.with_context(
                    checkin=reservation.checkin,
                    checkout=reservation.checkout,
                    room_type_id=False,  # Allows to choose any available room
                    current_lines=reservation.reservation_line_ids.ids,
                    pricelist_id=reservation.pricelist_id.id,
                )
                reservation.allowed_room_ids = pms_property.free_room_ids

            else:
                reservation.allowed_room_ids = False

    @api.depends("reservation_type", "agency_id", "folio_id", "folio_id.agency_id")
    def _compute_partner_id(self):
        for reservation in self:
            if not reservation.partner_id:
                if reservation.folio_id and reservation.folio_id.partner_id:
                    reservation.partner_id = reservation.folio_id.partner_id
                elif reservation.agency_id and reservation.agency_id.invoice_to_agency:
                    reservation.partner_id = reservation.agency_id
                elif not reservation.folio_id and not reservation.agency_id:
                    reservation.partner_id = False

    @api.depends("checkin", "checkout")
    def _compute_reservation_line_ids(self):
        for reservation in self:
            cmds = []
            if reservation.checkout and reservation.checkin:
                days_diff = (reservation.checkout - reservation.checkin).days
                for i in range(0, days_diff):
                    idate = reservation.checkin + datetime.timedelta(days=i)
                    old_line = reservation.reservation_line_ids.filtered(
                        lambda r: r.date == idate
                    )
                    if not old_line:
                        cmds.append(
                            (
                                0,
                                False,
                                {"date": idate},
                            )
                        )
                reservation.reservation_line_ids -= (
                    reservation.reservation_line_ids.filtered_domain(
                        [
                            "|",
                            ("date", ">=", reservation.checkout),
                            ("date", "<", reservation.checkin),
                        ]
                    )
                )
                reservation.reservation_line_ids = cmds
            else:
                if not reservation.reservation_line_ids:
                    reservation.reservation_line_ids = False
            reservation.check_in_out_dates()

    @api.depends("board_service_room_id")
    def _compute_service_ids(self):
        for reservation in self:
            board_services = []
            old_board_lines = reservation.service_ids.filtered_domain(
                [
                    ("is_board_service", "=", True),
                ]
            )
            # Avoid recalculating services if the boardservice has not changed
            if (
                old_board_lines
                and reservation.board_service_room_id
                == reservation._origin.board_service_room_id
            ):
                return
            if reservation.board_service_room_id:
                board = self.env["pms.board.service.room.type"].browse(
                    reservation.board_service_room_id.id
                )
                for line in board.board_service_line_ids:
                    res = {
                        "product_id": line.product_id.id,
                        "is_board_service": True,
                        "folio_id": reservation.folio_id.id,
                        "reservation_id": reservation.id,
                    }
                    board_services.append((0, False, res))
                reservation.service_ids -= old_board_lines
                reservation.service_ids = board_services
            elif old_board_lines:
                reservation.service_ids -= old_board_lines

    @api.depends("partner_id", "agency_id")
    def _compute_pricelist_id(self):
        for reservation in self:
            if reservation.agency_id and reservation.agency_id.apply_pricelist:
                reservation.pricelist_id = (
                    reservation.agency_id.property_product_pricelist
                )
            elif (
                reservation.partner_id
                and reservation.partner_id.property_product_pricelist
            ):
                reservation.pricelist_id = (
                    reservation.partner_id.property_product_pricelist
                )
            elif not reservation.pricelist_id.id:
                if reservation.folio_id and reservation.folio_id.pricelist_id:
                    reservation.pricelist_id = reservation.folio_id.pricelist_id
                else:
                    reservation.pricelist_id = (
                        reservation.pms_property_id.default_pricelist_id
                    )

    @api.depends("pricelist_id", "room_type_id")
    def _compute_show_update_pricelist(self):
        for reservation in self:
            if (
                sum(reservation.reservation_line_ids.mapped("price")) > 0
                and (
                    reservation.pricelist_id
                    and reservation._origin.pricelist_id != reservation.pricelist_id
                )
                or (
                    reservation.room_type_id
                    and reservation._origin.room_type_id != reservation.room_type_id
                )
            ):
                reservation.show_update_pricelist = True
            else:
                reservation.show_update_pricelist = False

    @api.depends("adults")
    def _compute_checkin_partner_ids(self):
        for reservation in self:
            assigned_checkins = reservation.checkin_partner_ids.filtered(
                lambda c: c.state in ("precheckin", "onboard", "done")
            )
            unassigned_checkins = reservation.checkin_partner_ids.filtered(
                lambda c: c.state == "draft"
            )
            leftover_unassigneds_count = (
                len(assigned_checkins) + len(unassigned_checkins) - reservation.adults
            )
            if len(assigned_checkins) > reservation.adults:
                raise UserError(
                    _("Remove some of the leftover assigned checkins first")
                )
            elif leftover_unassigneds_count > 0:
                for i in range(0, leftover_unassigneds_count):
                    reservation.checkin_partner_ids = [(2, unassigned_checkins[i].id)]
            elif reservation.adults > len(reservation.checkin_partner_ids):
                checkins_lst = []
                count_new_checkins = reservation.adults - len(
                    reservation.checkin_partner_ids
                )
                for _i in range(0, count_new_checkins):
                    checkins_lst.append(
                        (
                            0,
                            False,
                            {
                                "reservation_id": reservation.id,
                            },
                        )
                    )
                reservation.checkin_partner_ids = checkins_lst
            elif reservation.adults == 0:
                reservation.checkin_partner_ids = False

    @api.depends("checkin_partner_ids", "checkin_partner_ids.state")
    def _compute_count_pending_arrival(self):
        for reservation in self:
            reservation.count_pending_arrival = len(
                reservation.checkin_partner_ids.filtered(
                    lambda c: c.state in ("draft", "precheckin")
                )
            )

    @api.depends("count_pending_arrival")
    def _compute_checkins_ratio(self):
        self.checkins_ratio = 0
        for reservation in self.filtered(lambda r: r.adults > 0):
            reservation.checkins_ratio = (
                (reservation.adults - reservation.count_pending_arrival)
                * 100
                / reservation.adults
            )

    @api.depends("checkin_partner_ids", "checkin_partner_ids.state")
    def _compute_pending_checkin_data(self):
        for reservation in self:
            reservation.pending_checkin_data = len(
                reservation.checkin_partner_ids.filtered(lambda c: c.state == "draft")
            )

    @api.depends("pending_checkin_data")
    def _compute_ratio_checkin_data(self):
        self.ratio_checkin_data = 0
        for reservation in self.filtered(
            lambda r: r.adults > 0 and r.state != "cancel"
        ):
            reservation.ratio_checkin_data = (
                (reservation.adults - reservation.pending_checkin_data)
                * 100
                / reservation.adults
            )

    def _compute_allowed_checkin(self):
        # Reservations still pending entry today
        for record in self:
            record.allowed_checkin = (
                True
                if (
                    record.state in ["draft", "confirm", "arrival_delayed"]
                    and record.checkin <= fields.Date.today()
                )
                else False
            )

    def _compute_allowed_checkout(self):
        # Reservations still pending checkout today
        for record in self:
            record.allowed_checkout = (
                True
                if (
                    record.state in ["onboard", "departure_delayed"]
                    and record.checkout >= fields.Date.today()
                )
                else False
            )

    def _compute_allowed_cancel(self):
        # Reservations can be cancelled
        for record in self:
            record.allowed_cancel = (
                True
                if (record.state not in ["cancel", "done", "departure_delayed"])
                else False
            )

    def _compute_ready_for_checkin(self):
        # Reservations with hosts data enought to checkin
        for record in self:
            record.ready_for_checkin = (
                record.allowed_checkin
                and len(
                    record.checkin_partner_ids.filtered(
                        lambda c: c.state == "precheckin"
                    )
                )
                >= 1
            )

    def _compute_access_url(self):
        super(PmsReservation, self)._compute_access_url()
        for reservation in self:
            reservation.access_url = "/my/reservations/%s" % (reservation.id)

    @api.depends("reservation_line_ids")
    def _compute_checkin(self):
        """
        Allows to calculate the checkin by default or when the create
        specifically indicates the lines of the reservation
        """
        for record in self:
            if record.reservation_line_ids:
                checkin_line_date = min(record.reservation_line_ids.mapped("date"))
                # check if the checkin was created directly as reservation_line_id:
                if checkin_line_date != record.checkin:
                    record.checkin = checkin_line_date
            elif not record.checkin:
                # default checkout other folio reservations or today
                if len(record.folio_id.reservation_ids) > 1:
                    record.checkin = record.folio_id.reservation_ids[0].checkin
                else:
                    record.checkin = fields.date.today()
            record.check_in_out_dates()

    @api.depends("reservation_line_ids", "checkin")
    def _compute_checkout(self):
        """
        Allows to calculate the checkout by default or when the create
        specifically indicates the lines of the reservation
        """
        for record in self:
            if record.reservation_line_ids:
                checkout_line_date = max(
                    record.reservation_line_ids.mapped("date")
                ) + datetime.timedelta(days=1)
                # check if the checkout was created directly as reservation_line_id:
                if checkout_line_date != record.checkout:
                    record.checkout = checkout_line_date
            # default checkout if checkin is set
            elif record.checkin and not record.checkout:
                if len(record.folio_id.reservation_ids) > 1:
                    record.checkin = record.folio_id.reservation_ids[0].checkout
                else:
                    record.checkout = record.checkin + datetime.timedelta(days=1)
            elif not record.checkout:
                record.checkout = False
            # date checking
            record.check_in_out_dates()

    @api.depends("pms_property_id", "folio_id")
    def _compute_arrival_hour(self):
        for record in self:
            if not record.arrival_hour and record.pms_property_id:
                default_arrival_hour = record.pms_property_id.default_arrival_hour
                if (
                    record.folio_id
                    and record.folio_id.reservation_ids
                    and record.folio_id.reservation_ids[0].arrival_hour
                ):
                    record.arrival_hour = record.folio_id.reservation_ids[
                        0
                    ].arrival_hour
                else:
                    record.arrival_hour = default_arrival_hour
            elif not record.arrival_hour:
                record.arrival_hour = False

    @api.depends("pms_property_id", "folio_id")
    def _compute_departure_hour(self):
        for record in self:
            if not record.departure_hour and record.pms_property_id:
                default_departure_hour = record.pms_property_id.default_departure_hour
                if (
                    record.folio_id
                    and record.folio_id.reservation_ids
                    and record.folio_id.reservation_ids[0].departure_hour
                ):
                    record.departure_hour = record.folio_id.reservation_ids[
                        0
                    ].departure_hour
                else:
                    record.departure_hour = default_departure_hour
            elif not record.departure_hour:
                record.departure_hour = False

    @api.depends("agency_id")
    def _compute_commission_percent(self):
        for reservation in self:
            if reservation.agency_id:
                reservation.commission_percent = (
                    reservation.agency_id.default_commission
                )
            else:
                reservation.commission_percent = 0

    @api.depends("commission_percent", "price_total")
    def _compute_commission_amount(self):
        for reservation in self:
            if reservation.commission_percent > 0:
                reservation.commission_amount = (
                    reservation.price_total * reservation.commission_percent / 100
                )
            else:
                reservation.commission_amount = 0

    # REVIEW: Dont run with set room_type_id -> room_id(compute)-> No set adults¿?
    @api.depends("preferred_room_id")
    def _compute_adults(self):
        for reservation in self:
            if reservation.preferred_room_id:
                if reservation.adults == 0:
                    reservation.adults = reservation.preferred_room_id.capacity
            elif not reservation.adults:
                reservation.adults = 0

    @api.depends("reservation_line_ids", "reservation_line_ids.room_id")
    def _compute_splitted(self):
        # REVIEW: Updating preferred_room_id here avoids cyclical dependency
        for reservation in self:
            room_ids = reservation.reservation_line_ids.mapped("room_id.id")
            if len(room_ids) > 1:
                reservation.splitted = True
                reservation.preferred_room_id = False
            else:
                reservation.splitted = False
                if room_ids:
                    reservation.preferred_room_id = room_ids[0]

    @api.depends(
        "sale_line_ids",
        "sale_line_ids.invoice_status",
    )
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a Reservation. Possible statuses:
        Base on folio sale line invoice status
        """
        for line in self:
            states = list(set(line.sale_line_ids.mapped("invoice_status")))
            if len(states) == 1:
                line.invoice_status = states[0]
            elif len(states) >= 1:
                if "to_invoice" in states:
                    line.invoice_status = "to_invoice"
                elif "invoiced" in states:
                    line.invoice_status = "invoiced"
                else:
                    line.invoice_status = "no"
            else:
                line.invoice_status = "no"

    @api.depends("reservation_line_ids")
    def _compute_nights(self):
        for res in self:
            res.nights = len(res.reservation_line_ids)

    @api.depends("service_ids.price_total", "services_discount")
    def _compute_price_services(self):
        for record in self:
            record.price_services = (
                sum(record.mapped("service_ids.price_total")) - record.services_discount
            )

    @api.depends("price_services", "price_total")
    def _compute_price_room_services_set(self):
        for record in self:
            record.price_room_services_set = record.price_services + record.price_total

    @api.depends(
        "reservation_line_ids.discount",
        "reservation_line_ids.cancel_discount",
    )
    def _compute_discount(self):
        for record in self:
            discount = 0
            for line in record.reservation_line_ids:
                first_discount = line.price * ((line.discount or 0.0) * 0.01)
                price = line.price - first_discount
                cancel_discount = price * ((line.cancel_discount or 0.0) * 0.01)
                discount += first_discount + cancel_discount

            record.discount = discount

    @api.depends("service_ids.discount")
    def _compute_services_discount(self):
        for record in self:
            services_discount = 0
            for service in record.service_ids:
                services_discount += service.discount
            record.services_discount = services_discount

    @api.depends("reservation_line_ids.price", "discount", "tax_ids")
    def _compute_amount_reservation(self):
        """
        Compute the amounts of the reservation.
        """
        for record in self:
            amount_room = sum(record.reservation_line_ids.mapped("price"))
            if amount_room > 0:
                product = record.room_type_id.product_id
                price = amount_room - record.discount
                taxes = record.tax_ids.compute_all(
                    price, record.currency_id, 1, product=product
                )
                record.update(
                    {
                        "price_tax": sum(
                            t.get("amount", 0.0) for t in taxes.get("taxes", [])
                        ),
                        "price_total": taxes["total_included"],
                        "price_subtotal": taxes["total_excluded"],
                    }
                )
            else:
                record.update(
                    {
                        "price_tax": 0,
                        "price_total": 0,
                        "price_subtotal": 0,
                    }
                )

    def _compute_shared_folio(self):
        # Has this reservation more charges associates in folio?,
        # Yes?, then, this is share folio ;)
        for record in self:
            if record.folio_id:
                record.shared_folio = len(record.folio_id.reservation_ids) > 1 or any(
                    record.folio_id.service_ids.filtered(
                        lambda x: x.reservation_id.id != record.id
                    )
                )
            else:
                record.shared_folio = False

    @api.depends("partner_id", "partner_id.name")
    def _compute_partner_name(self):
        for record in self:
            self.env["pms.folio"]._apply_partner_name(record)

    @api.depends("partner_id", "partner_id.email")
    def _compute_email(self):
        for record in self:
            self.env["pms.folio"]._apply_email(record)

    @api.depends("partner_id", "partner_id.mobile")
    def _compute_mobile(self):
        for record in self:
            self.env["pms.folio"]._apply_mobile(record)

    @api.depends(
        "partner_name",
        "email",
        "mobile",
        "partner_id",
    )
    def _compute_partner_incongruences(self):
        fields_mapping = {
            "partner_name": "name",
            "email": "email",
            "mobile": "mobile",
        }
        for record in self:
            incongruous_fields = False
            if record.partner_id:
                for k, v in fields_mapping.items():
                    if record.partner_id[v] and record.partner_id[v] != record[k]:
                        if not incongruous_fields:
                            incongruous_fields = v
                        else:
                            incongruous_fields += ", " + v
                if incongruous_fields:
                    record.partner_incongruences = (
                        incongruous_fields + " field/s don't correspond to saved host"
                    )
                else:
                    record.partner_incongruences = False
            else:
                record.partner_incongruences = False

    def _compute_checkin_partner_count(self):
        for record in self:
            if record.reservation_type != "out":
                record.checkin_partner_count = len(record.checkin_partner_ids)
                record.checkin_partner_pending_count = record.adults - len(
                    record.checkin_partner_ids
                )
            else:
                record.checkin_partner_count = 0
                record.checkin_partner_pending_count = 0

    @api.depends("room_type_id")
    def _compute_tax_ids(self):
        for record in self:
            record = record.with_company(record.company_id)
            product = self.env["product.product"].browse(
                record.room_type_id.product_id.id
            )
            record.tax_ids = product.taxes_id.filtered(
                lambda t: t.company_id == record.env.company
            )

    @api.depends("reservation_line_ids", "reservation_line_ids.room_id")
    def _compute_rooms(self):
        self.rooms = False
        for reservation in self:
            if reservation.splitted:
                reservation.rooms = ", ".join(
                    [r for r in reservation.reservation_line_ids.mapped("room_id.name")]
                )
            else:
                reservation.rooms = reservation.preferred_room_id.name

    def _search_allowed_checkin(self, operator, value):
        if operator not in ("=",):
            raise UserError(
                _("Invalid domain operator %s for left of checkin", operator)
            )

        if value not in (True,):
            raise UserError(
                _("Invalid domain right operand %s for left of checkin", value)
            )

        today = fields.Date.context_today(self)
        return [
            ("state", "in", ("draft", "confirm", "arrival_delayed")),
            ("checkin", "<=", today),
        ]

    def _search_allowed_checkout(self, operator, value):
        if operator not in ("=",):
            raise UserError(
                _("Invalid domain operator %s for left of checkout", operator)
            )

        if value not in (True,):
            raise UserError(
                _("Invalid domain right operand %s for left of checkout", value)
            )

        today = fields.Date.context_today(self)
        return [
            ("state", "in", ("onboard", "departure_delayed")),
            ("checkout", ">=", today),
        ]

    def _search_allowed_cancel(self, operator, value):
        if operator not in ("=",):
            raise UserError(
                _("Invalid domain operator %s for left of cancel", operator)
            )

        if value not in (True,):
            raise UserError(
                _("Invalid domain right operand %s for left of cancel", value)
            )
        return [
            ("state", "not in", ("cancel", "done", "departure_delayed")),
        ]

    def _search_checkin_partner_pending(self, operator, value):
        self.ensure_one()
        recs = self.search([]).filtered(lambda x: x.checkin_partner_pending_count > 0)
        return [("id", "in", [x.id for x in recs])] if recs else []

    def _get_default_segmentation(self):
        folio = False
        segmentation_ids = False
        if "folio_id" in self._context:
            folio = self.env["pms.folio"].search(
                [("id", "=", self._context["folio_id"])]
            )
        if folio and folio.segmentation_ids:
            segmentation_ids = folio.segmentation_ids
        return segmentation_ids

    def check_in_out_dates(self):
        """
        1.-When date_order is less then checkin date or
        Checkout date should be greater than the checkin date.
        3.-Check the reservation dates are not occuped
        """
        for record in self:
            if (
                record.checkout
                and record.checkout
                and record.checkin >= record.checkout
            ):
                raise UserError(
                    _(
                        "Room line Check In Date Should be \
                    less than the Check Out Date!"
                    )
                )

    @api.constrains("reservation_line_ids")
    def check_consecutive_dates(self):
        """
        simply convert date objects to integers using the .toordinal() method
        of datetime objects. The difference between the maximum and minimum value
        of the set of ordinal dates is one more than the length of the set
        """
        for record in self:
            if record.reservation_line_ids and len(record.reservation_line_ids) > 1:
                dates = record.reservation_line_ids.mapped("date")
                date_ints = {d.toordinal() for d in dates}
                if not (max(date_ints) - min(date_ints) == len(date_ints) - 1):
                    raise ValidationError(_("Reservation dates should be consecutives"))

    # @api.constrains("checkin_partner_ids", "adults")
    # def _max_checkin_partner_ids(self):
    #     for record in self:
    #         if len(record.checkin_partner_ids) > record.adults:
    #             raise models.ValidationError(
    #                 _("The room already is completed (%s)", record.name)
    #             )

    @api.constrains("adults")
    def _check_adults(self):
        for record in self:
            extra_bed = record.service_ids.filtered(
                lambda r: r.product_id.is_extra_bed is True
            )
            for room in record.reservation_line_ids.room_id:
                if record.adults + record.children_occupying > room.get_capacity(
                    sum(extra_bed.mapped("product_qty"))
                ):
                    raise ValidationError(
                        _(
                            "Persons can't be higher than room capacity (%s)",
                            record.name,
                        )
                    )

    @api.constrains("state")
    def _check_onboard_reservation(self):
        for record in self:
            if (
                not record.checkin_partner_ids.filtered(lambda c: c.state == "onboard")
                and record.state == "onboard"
            ):
                raise ValidationError(
                    _("No person from reserve %s has arrived", record.name)
                )

    @api.constrains("arrival_hour")
    def _check_arrival_hour(self):
        for record in self:
            if record.arrival_hour:
                try:
                    time.strptime(record.arrival_hour, "%H:%M")
                    return True
                except ValueError:
                    raise ValidationError(
                        _("Format Arrival Hour (HH:MM) Error: %s", record.arrival_hour)
                    )

    @api.constrains("departure_hour")
    def _check_departure_hour(self):
        for record in self:
            if record.departure_hour:
                try:
                    time.strptime(record.departure_hour, "%H:%M")
                    return True
                except ValueError:
                    raise ValidationError(
                        _(
                            "Format Departure Hour (HH:MM) Error: %s",
                            record.departure_hour,
                        )
                    )

    @api.constrains("agency_id")
    def _no_agency_as_agency(self):
        for record in self:
            if record.agency_id and not record.agency_id.is_agency:
                raise ValidationError(_("booking agency with wrong configuration: "))

    # Action methods
    def open_partner(self):
        """ Utility method used to add an "View Customer" button in reservation views """
        self.ensure_one()
        partner_form_id = self.env.ref("pms.view_partner_data_form").id
        return {
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "view_mode": "form",
            "views": [(partner_form_id, "form")],
            "res_id": self.partner_id.id,
            "target": "new",
            "flags": {"form": {"action_buttons": True}},
        }

    def print_all_checkins(self):
        checkins = self.env["pms.checkin.partner"]
        for record in self:
            checkins += record.checkin_partner_ids.filtered(
                lambda s: s.state in ("precheckin", "onboard", "done")
            )
        if checkins:
            return self.env.ref("pms.action_traveller_report").report_action(checkins)
        else:
            raise ValidationError(_("There are no checkins to print"))

    def open_folio(self):
        action = self.env.ref("pms.open_pms_folio1_form_tree_all").sudo().read()[0]
        if self.folio_id:
            action["views"] = [(self.env.ref("pms.pms_folio_view_form").id, "form")]
            action["res_id"] = self.folio_id.id
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action

    def open_reservation_form(self):
        action = self.env.ref("pms.open_pms_reservation_form_tree_all").sudo().read()[0]
        action["views"] = [(self.env.ref("pms.pms_reservation_view_form").id, "form")]
        action["res_id"] = self.id
        return action

    def action_pay_folio(self):
        self.ensure_one()
        return self.folio_id.action_pay()

    def open_reservation_wizard(self):
        pms_property = self.pms_property_id
        pms_property = pms_property.with_context(
            checkin=self.checkin,
            checkout=self.checkout,
            current_lines=self.reservation_line_ids.ids,
            pricelist_id=self.pricelist_id.id,
        )
        rooms_available = pms_property.free_room_ids

        # REVIEW: check capacity room
        return {
            "view_type": "form",
            "view_mode": "form",
            "name": "Unify the reservation",
            "res_model": "pms.reservation.split.join.swap.wizard",
            "target": "new",
            "type": "ir.actions.act_window",
            "context": {
                "rooms_available": rooms_available.ids,
            },
        }

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        if args is None:
            args = []
        if not (name == "" and operator == "ilike"):
            args += [
                "|",
                ("name", operator, name),
                ("folio_id.name", operator, name),
                ("preferred_room_id.name", operator, name),
            ]
        return super(PmsReservation, self).name_search(
            name="", args=args, operator="ilike", limit=limit
        )

    def name_get(self):
        result = []
        for res in self:
            name = u"{} ({})".format(res.name, res.rooms if res.rooms else "No room")
            result.append((res.id, name))
        return result

    @api.model
    def create(self, vals):
        if vals.get("folio_id"):
            folio = self.env["pms.folio"].browse(vals["folio_id"])
            default_vals = {"pms_property_id": folio.pms_property_id.id}
            if folio.partner_id:
                default_vals["partner_id"] = folio.partner_id.id
            elif folio.partner_name:
                default_vals["partner_name"] = folio.partner_name
                default_vals["mobile"] = folio.mobile
                default_vals["email"] = folio.email
            else:
                raise ValidationError(_("Partner contact name is required"))
            vals.update(default_vals)
        elif "pms_property_id" in vals and (
            "partner_name" in vals or "partner_id" in vals or "agency_id" in vals
        ):
            folio_vals = {
                "pms_property_id": vals["pms_property_id"],
            }
            if vals.get("partner_id"):
                folio_vals["partner_id"] = vals.get("partner_id")
            elif vals.get("agency_id"):
                folio_vals["agency_id"] = vals.get("agency_id")
            elif vals.get("partner_name"):
                folio_vals["partner_name"] = vals.get("partner_name")
                folio_vals["mobile"] = vals.get("mobile")
                folio_vals["email"] = vals.get("email")
            else:
                raise ValidationError(_("Partner contact name is required"))
            # Create the folio in case of need
            # (To allow to create reservations direct)
            folio = self.env["pms.folio"].create(folio_vals)
            vals.update(
                {
                    "folio_id": folio.id,
                    "reservation_type": vals.get("reservation_type"),
                }
            )
        else:
            raise ValidationError(_("The Property are mandatory in the reservation"))
        if vals.get("name", _("New")) == _("New") or "name" not in vals:
            pms_property_id = (
                self.env.user.get_active_property_ids()[0]
                if "pms_property_id" not in vals
                else vals["pms_property_id"]
            )
            pms_property = self.env["pms.property"].browse(pms_property_id)
            vals["name"] = pms_property.reservation_sequence_id._next_do()
        record = super(PmsReservation, self).create(vals)
        if record.preconfirm:
            record.confirm()
        return record

    def update_prices(self):
        self.ensure_one()
        for line in self.reservation_line_ids:
            line.with_context(force_recompute=True)._compute_price()
        self.show_update_pricelist = False
        self.message_post(
            body=_(
                """Prices have been recomputed according to pricelist <b>%s</b>
                 and room type <b>%s</b>""",
                self.pricelist_id.display_name,
                self.room_type_id.name,
            )
        )

    @api.model
    def autocheckout(self):
        reservations = self.env["pms.reservation"].search(
            [
                ("state", "not in", ["done", "cancel"]),
                ("checkout", "<", fields.Date.today()),
            ]
        )
        for res in reservations:
            res.action_reservation_checkout()
        res_without_checkin = reservations.filtered(lambda r: r.state != "onboard")
        for res in res_without_checkin:
            msg = _("No checkin was made for this reservation")
            res.message_post(subject=_("No Checkins!"), subtype="mt_comment", body=msg)
        return True

    @api.model
    def update_daily_priority_reservation(self):
        reservations = self.env["pms.reservation"].search([("priority", "<", 1000)])
        reservations._compute_priority()
        return True

    def overbooking_button(self):
        self.ensure_one()
        self.overbooking = not self.overbooking

    def confirm(self):
        for record in self:
            vals = {}
            if record.checkin_partner_ids.filtered(lambda c: c.state == "onboard"):
                vals.update({"state": "onboard"})
            else:
                vals.update({"state": "confirm"})
            record.write(vals)
            record.reservation_line_ids.update({"cancel_discount": 0})
            if record.folio_id.state != "confirm":
                record.folio_id.action_confirm()
        return True

    def action_cancel(self):
        for record in self:
            # else state = cancel
            if not record.allowed_cancel:
                raise UserError(_("This reservation cannot be cancelled"))
            else:
                record.state = "cancel"
                record.folio_id._compute_amount()

    def action_assign(self):
        for record in self:
            record.to_assign = False

    @api.depends("state")
    def _compute_cancelled_reason(self):
        for record in self:
            # self.ensure_one()
            if record.state == "cancel":
                pricelist = record.pricelist_id
                if record._context.get("no_penalty", False):
                    record.cancelled_reason = "intime"
                    _logger.info("Modified Reservation - No Penalty")
                elif pricelist and pricelist.cancelation_rule_id:
                    tz_property = record.pms_property_id.tz
                    today = fields.Date.context_today(
                        record.with_context(tz=tz_property)
                    )
                    days_diff = (
                        fields.Date.from_string(record.checkin)
                        - fields.Date.from_string(today)
                    ).days
                    if days_diff < 0:
                        record.cancelled_reason = "noshow"
                    elif days_diff < pricelist.cancelation_rule_id.days_intime:
                        record.cancelled_reason = "late"
                    else:
                        record.cancelled_reason = "intime"
                else:
                    record.cancelled_reason = False

    def action_reservation_checkout(self):
        for record in self:
            if not record.allowed_checkout:
                raise UserError(_("This reservation cannot be check out"))
            record.state = "done"
            if record.checkin_partner_ids:
                record.checkin_partner_ids.filtered(
                    lambda check: check.state == "onboard"
                ).action_done()
        return True

    def action_checkin_partner_view(self):
        self.ensure_one()
        tree_id = self.env.ref("pms.pms_checkin_partner_reservation_view_tree").id
        return {
            "name": _("Register Partners"),
            "views": [[tree_id, "tree"]],
            "res_model": "pms.checkin.partner",
            "type": "ir.actions.act_window",
            "context": {
                "create": False,
                "edit": True,
                "popup": True,
            },
            "domain": [("reservation_id", "=", self.id), ("state", "=", "draft")],
            "search_view_id": [
                self.env.ref("pms.pms_checkin_partner_view_folio_search").id,
                "search",
            ],
            "target": "new",
        }

    def action_checkin_partner_onboard_view(self):
        self.ensure_one()
        kanban_id = self.env.ref("pms.pms_checkin_partner_kanban_view").id
        return {
            "name": _("Register Checkins"),
            "views": [[kanban_id, "kanban"]],
            "res_model": "pms.checkin.partner",
            "type": "ir.actions.act_window",
            "context": {
                "create": False,
                "edit": True,
                "popup": True,
            },
            "search_view_id": [
                self.env.ref("pms.pms_checkin_partner_view_folio_search").id,
                "search",
            ],
            "domain": [("reservation_id", "=", self.id)],
            "target": "new",
        }

    @api.model
    def auto_arrival_delayed(self):
        # No show when pass 1 day from checkin day
        arrival_delayed_reservations = self.env["pms.reservation"].search(
            [
                ("state", "in", ("draft", "confirm")),
                ("checkin", "<", fields.Date.today()),
            ]
        )
        arrival_delayed_reservations.state = "arrival_delayed"

    @api.model
    def auto_departure_delayed(self):
        # No checkout when pass checkout hour
        reservations = self.env["pms.reservation"].search(
            [
                ("state", "in", ("onboard",)),
                ("checkout", "<=", fields.Datetime.today()),
            ]
        )
        for reservation in reservations:
            if reservation.checkout_datetime <= fields.Datetime.now():
                reservations.state = "departure_delayed"

    def preview_reservation(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "target": "self",
            "url": self.get_portal_url(),
        }
