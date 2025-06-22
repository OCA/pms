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
    _order = "write_date desc, create_date desc"
    # TODO:
    #  consider near_to_checkin & pending_notifications to order
    _check_pms_properties_auto = True
    _check_company_auto = True

    name = fields.Text(
        string="Reservation Code",
        help="Reservation Code Identification",
        readonly=True,
    )
    external_reference = fields.Char(
        help="Reference of this folio in an external system",
        compute="_compute_external_reference",
        store=True,
        readonly=False,
    )
    folio_sequence = fields.Integer(
        help="Techinal field to get reservation name",
        readonly=True,
    )
    preferred_room_id = fields.Many2one(
        string="Room",
        help="It's the preferred room assigned to reservation, "
        "empty if reservation is splitted",
        copy=False,
        comodel_name="pms.room",
        ondelete="restrict",
        index=True,
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
        index=True,
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
        index=True,
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
        index=True,
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
        index=True,
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
        index=True,
        related="folio_id.agency_id",
        depends=["folio_id.agency_id"],
        tracking=True,
    )
    sale_channel_ids = fields.Many2many(
        string="Sale Channels",
        help="Sale Channels through which reservation lines were managed",
        store=True,
        compute="_compute_sale_channel_ids",
        comodel_name="pms.sale.channel",
    )
    sale_channel_origin_id = fields.Many2one(
        string="Sale Channel Origin",
        help="Sale Channel through which reservation was created, the original",
        default=lambda self: self._get_default_sale_channel_origin(),
        comodel_name="pms.sale.channel",
        index=True,
    )
    force_update_origin = fields.Boolean(
        string="Update Sale Channel Origin",
        help="This field is for force update in sale channel "
        "origin of folio and another reservations",
        store=True,
        readonly=False,
        compute="_compute_force_update_origin",
    )
    is_origin_channel_check_visible = fields.Boolean(
        string="Check force update origin visible",
        help="Technical field to make visible update " "origin channel check",
        store=True,
        readonly=False,
        compute="_compute_is_origin_channel_check_visible",
    )
    closure_reason_id = fields.Many2one(
        string="Closure Reason",
        help="Reason why the reservation cannot be made",
        related="folio_id.closure_reason_id",
        check_pms_properties=True,
        readonly=False,
    )
    out_service_description = fields.Text(
        string="Cause of out of service",
        help="Indicates the cause of out of service",
        related="folio_id.out_service_description",
        readonly=False,
    )
    company_id = fields.Many2one(
        string="Company",
        help="Company to which the reservation belongs",
        readonly=True,
        store=True,
        related="folio_id.company_id",
        index=True,
    )
    pms_property_id = fields.Many2one(
        string="Pms Property",
        help="Property to which the reservation belongs",
        store=True,
        readonly=False,
        related="folio_id.pms_property_id",
        comodel_name="pms.property",
        index=True,
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
        compute="_compute_board_service_ids",
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
        index=True,
        domain="[('is_pms_available', '=', True)]",
    )
    user_id = fields.Many2one(
        string="Reception Manager",
        help="The reception manager in the folio",
        readonly=False,
        index=True,
        store=True,
        comodel_name="res.users",
        ondelete="restrict",
        compute="_compute_user_id",
        tracking=True,
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
        domain="[('is_used_in_checkin', '=', True)]",
    )
    currency_id = fields.Many2one(
        related="pricelist_id.currency_id",
        depends=["pricelist_id"],
        store=True,
        ondelete="restrict",
    )
    tax_ids = fields.Many2many(
        string="Taxes",
        help="Taxes applied in the reservation",
        readonly=False,
        store=True,
        compute="_compute_tax_ids",
        comodel_name="account.tax",
        domain=["|", ("active", "=", False), ("active", "=", True)],
    )
    adults = fields.Integer(
        help="List of adults there in guest list",
        readonly=False,
        store=True,
        compute="_compute_adults",
        tracking=True,
    )
    children_occupying = fields.Integer(
        help="Number of children there in guest list whose presence counts",
    )
    children = fields.Integer(
        help="Number total of children there in guest list,"
        "whose presence counts or not",
        readonly=False,
        tracking=True,
    )
    to_assign = fields.Boolean(
        help="It is True if the room of the reservation has been assigned "
        "automatically, False if it was confirmed by a person in charge",
        default=True,
    )
    state = fields.Selection(
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
    cancel_datetime = fields.Datetime(
        string="Cancel Date",
        help="Date when the reservation was cancelled",
        readonly=True,
        copy=False,
    )
    reservation_type = fields.Selection(
        help="Type of reservations. It can be 'normal', 'staff' or 'out of service",
        store=True,
        readonly=False,
        compute="_compute_reservation_type",
        selection=[("normal", "Normal"), ("staff", "Staff"), ("out", "Out of Service")],
    )
    splitted = fields.Boolean(
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
    credit_card_details = fields.Text(related="folio_id.credit_card_details")
    cancelled_reason = fields.Selection(
        string="Reason of cancellation",
        help="Field indicating type of cancellation. "
        "It can be 'late', 'intime' or 'noshow'",
        copy=False,
        store=True,
        selection=[
            ("late", "Late"),
            ("intime", "In time"),
            ("noshow", "No Show"),
            ("modified", "Modified"),
        ],
        tracking=True,
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
        help="Arrival Hour (HH:MM)",
        readonly=False,
        store=True,
        compute="_compute_arrival_hour",
    )
    departure_hour = fields.Char(
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
        compute="_compute_overbooking",
        store=True,
    )
    nights = fields.Integer(
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
        help="indicates that some partner fields \
            on the reservation do not correspond to that of \
            the associated partner",
        compute="_compute_partner_incongruences",
    )
    partner_requests = fields.Text(
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
        help="The status of the invoices in folio. Can be 'invoiced',"
        " 'to_invoice' or 'no'.",
        store=True,
        readonly=True,
        selection=[
            ("invoiced", "Fully Invoiced"),
            ("to_invoice", "To Invoice"),
            ("no", "Nothing to Invoice"),
        ],
        compute="_compute_invoice_status",
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
        help="Discount of total price in reservation",
        readonly=False,
        store=True,
        digits=("Discount"),
        compute="_compute_discount",
        tracking=True,
    )

    services_discount = fields.Float(
        help="Services discount",
        readonly=False,
        store=True,
        digits=("Discount"),
        compute="_compute_services_discount",
        tracking=True,
    )
    date_order = fields.Datetime(
        help="Order date of reservation",
        default=fields.Datetime.now,
        store=True,
        readonly=False,
    )

    check_adults = fields.Boolean(
        help="Internal field to force room capacity validations",
        compute="_compute_check_adults",
        readonly=False,
        store=True,
    )

    possible_existing_customer_ids = fields.One2many(
        string="Possible existing customer",
        compute="_compute_possible_existing_customer_ids",
        comodel_name="res.partner",
        inverse_name="reservation_possible_customer_id",
    )

    avoid_mails = fields.Boolean(
        string="Avoid comunication mails",
        help="Field to indicate not sent mail comunications",
        compute="_compute_avoid_mails",
        readonly=False,
        store=True,
    )

    to_send_confirmation_mail = fields.Boolean(
        compute="_compute_to_send_confirmation_mail",
        readonly=False,
        store=True,
    )

    to_send_modification_mail = fields.Boolean(
        compute="_compute_to_send_modification_mail",
        readonly=False,
        store=True,
    )

    to_send_exit_mail = fields.Boolean(
        compute="_compute_to_send_exit_mail",
        readonly=False,
        store=True,
    )

    to_send_cancelation_mail = fields.Boolean(
        compute="_compute_to_send_cancelation_mail",
        readonly=False,
        store=True,
    )

    overnight_room = fields.Boolean(
        related="room_type_id.overnight_room",
        store=True,
    )
    # TODO: This field is deprecated
    lang = fields.Many2one(
        string="Language", comodel_name="res.lang", compute="_compute_lang"
    )
    blocked = fields.Boolean(
        help="Indicates if the reservation is blocked",
        default=False,
    )

    is_reselling = fields.Boolean(
        string="Reselling",
        help="Indicate if exists reselling in any reservation line",
        compute="_compute_is_reselling",
        store=True,
        readonly=False,
    )
    count_alternative_free_rooms = fields.Integer(
        compute="_compute_count_alternative_free_rooms",
    )

    @api.depends("folio_id", "folio_id.external_reference")
    def _compute_external_reference(self):
        for reservation in self:
            if not reservation.external_reference:
                reservation.external_reference = (
                    reservation._get_reservation_external_reference()
                )

    def _get_reservation_external_reference(self):
        self.ensure_one()
        folio = self.folio_id
        if folio and folio.external_reference:
            return folio.external_reference
        else:
            return False

    def _compute_date_order(self):
        for record in self:
            record.date_order = datetime.datetime.today()

    @api.depends(
        "service_ids",
        "service_ids.service_line_ids",
        "service_ids.service_line_ids.product_id",
        "service_ids.service_line_ids.day_qty",
        "reservation_line_ids",
        "reservation_line_ids.room_id",
    )
    def _compute_check_adults(self):
        for record in self:
            record.check_adults = True

    @api.depends("pricelist_id", "room_type_id")
    def _compute_board_service_room_id(self):
        for reservation in self:
            if reservation.pricelist_id and reservation.room_type_id:
                board_service_default = (
                    reservation.room_type_id.get_default_board_service(
                        pms_property_id=reservation.pms_property_id.id,
                        room_type_id=reservation.room_type_id.id,
                        pricelist_id=reservation.pricelist_id.id,
                    )
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
        "room_type_id",
        "pricelist_id",
        "pms_property_id",
    )
    def _compute_allowed_room_ids(self):
        for reservation in self:
            if reservation.checkin and reservation.checkout:
                if reservation.overbooking or reservation.state in ("cancel"):
                    reservation.allowed_room_ids = self.env["pms.room"].search(
                        [
                            ("active", "=", True),
                        ]
                    )
                    return
                pms_property = reservation.pms_property_id
                pms_property = pms_property.with_context(
                    checkin=reservation.checkin,
                    checkout=reservation.checkout,
                    room_type_id=False,  # Allows to choose any available room
                    current_lines=reservation.reservation_line_ids.ids,
                    pricelist_id=reservation.pricelist_id.id,
                    class_id=(
                        reservation.room_type_id.class_id.id
                        if reservation.room_type_id
                        else False
                    ),
                    real_avail=True,
                )
                reservation.allowed_room_ids = pms_property.free_room_ids
            else:
                reservation.allowed_room_ids = False

    @api.depends(
        "reservation_type",
        "folio_id",
        "folio_id.agency_id",
        "partner_name",
        "email",
        "mobile",
    )
    def _compute_partner_id(self):
        for reservation in self:
            if not reservation.partner_id:
                if reservation.reservation_type == "out":
                    reservation.partner_id = False
                elif reservation.folio_id and reservation.folio_id.partner_id:
                    reservation.partner_id = reservation.folio_id.partner_id
                elif not reservation.partner_id:
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
                        lambda r, idate=idate: r.date == idate
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
    def _compute_board_service_ids(self):
        if self.env.context.get("skip_compute_board_service_ids", False):
            return
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
                    if (reservation.adults and line.adults) or (
                        reservation.children and line.children
                    ):
                        data = {
                            "product_id": line.product_id.id,
                            "is_board_service": True,
                            "folio_id": reservation.folio_id.id,
                            "reservation_id": reservation.id,
                            "board_service_line_id": line.id,
                        }
                        board_services.append((0, False, data))
                reservation.service_ids -= old_board_lines
                reservation.service_ids = board_services
            elif old_board_lines:
                reservation.service_ids -= old_board_lines

    @api.depends("partner_id", "agency_id")
    def _compute_pricelist_id(self):
        for reservation in self:
            is_new = not reservation.pricelist_id or isinstance(
                reservation.id, models.NewId
            )
            if reservation.reservation_type == "out":
                reservation.pricelist_id = False
            elif (
                is_new
                and reservation.agency_id
                and reservation.agency_id.apply_pricelist
            ):
                reservation.pricelist_id = (
                    reservation.agency_id.property_product_pricelist
                )
            # only change de pricelist if the reservation is not yet saved
            # and the partner has a pricelist default
            elif (
                is_new
                and reservation.partner_id
                and reservation.partner_id.property_product_pricelist
                and reservation.partner_id.property_product_pricelist.is_pms_available
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

    @api.depends("folio_id", "pms_property_id")
    def _compute_user_id(self):
        active_user_id = self.env.uid
        for res in self:
            if not res.user_id and not res.folio_id:
                property_users = res.pms_property_id.member_ids.filtered(
                    lambda u: u.pms_role == "reception"
                ).mapped("user_id")
                if property_users:
                    if active_user_id in property_users.ids:
                        res.user_id = active_user_id
                    elif property_users:
                        res.user_id = property_users[0]
                    else:
                        res.user_id = active_user_id or res.pms_property_id.user_id

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

    @api.depends("adults", "children")
    def _compute_checkin_partner_ids(self):
        for reservation in self:
            occupancy = (
                reservation.adults + reservation.children
                if reservation.reservation_type != "out"
                else 0
            )
            assigned_checkins = reservation.checkin_partner_ids.filtered(
                lambda c: c.state in ("precheckin", "onboard", "done")
            )
            unassigned_checkins = reservation.checkin_partner_ids.filtered(
                lambda c: c.state in ("dummy", "draft")
            )
            leftover_unassigneds_count = (
                len(assigned_checkins) + len(unassigned_checkins) - occupancy
            )
            if len(assigned_checkins) > occupancy:
                raise UserError(
                    _("Remove some of the leftover assigned checkins first")
                )
            elif leftover_unassigneds_count > 0:
                for i in range(0, leftover_unassigneds_count):
                    reservation.checkin_partner_ids = [(2, unassigned_checkins[i].id)]
            elif occupancy > len(reservation.checkin_partner_ids):
                checkins_lst = []
                count_new_checkins = occupancy - len(reservation.checkin_partner_ids)
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
            elif occupancy == 0:
                reservation.checkin_partner_ids = False

    @api.depends("checkin_partner_ids", "checkin_partner_ids.state")
    def _compute_count_pending_arrival(self):
        for reservation in self:
            reservation.count_pending_arrival = len(
                reservation.checkin_partner_ids.filtered(
                    lambda c: c.state in ("dummy", "draft", "precheckin")
                )
            )

    @api.depends("count_pending_arrival")
    def _compute_checkins_ratio(self):
        self.checkins_ratio = 0
        for reservation in self.filtered(lambda r: (r.adults + r.children) > 0):
            occupancy = reservation.adults + reservation.children
            reservation.checkins_ratio = (
                (occupancy - reservation.count_pending_arrival) * 100 / occupancy
            )

    @api.depends("checkin_partner_ids", "checkin_partner_ids.state")
    def _compute_pending_checkin_data(self):
        for reservation in self:
            reservation.pending_checkin_data = len(
                reservation.checkin_partner_ids.filtered(
                    lambda c: c.state in ("dummy", "draft")
                )
            )

    @api.depends("pending_checkin_data")
    def _compute_ratio_checkin_data(self):
        self.ratio_checkin_data = 0
        for reservation in self.filtered(
            lambda r: (r.adults + r.children) > 0 and r.state != "cancel"
        ):
            occupancy = reservation.adults + reservation.children
            reservation.ratio_checkin_data = (
                (occupancy - reservation.pending_checkin_data) * 100 / occupancy
            )

    def _compute_allowed_checkin(self):
        # Reservations still pending entry today
        for record in self:
            record.allowed_checkin = (
                True
                if (
                    record.reservation_type != "out"
                    and record.overnight_room
                    and record.state in ("draft", "confirm", "arrival_delayed")
                    and fields.Date.today() >= record.checkin
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
                    and fields.Date.today() >= record.checkout
                )
                else False
            )

    def _compute_allowed_cancel(self):
        # Reservations can be cancelled
        for record in self:
            record.allowed_cancel = (
                True if (record.state not in ["done", "onboard"]) else False
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

    # pylint: disable=W8110
    def _compute_access_url(self):
        super()._compute_access_url()
        for reservation in self:
            reservation.access_url = f"/my/reservations/{reservation.id}"

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

    # pylint: disable=W8110
    def _compute_precheckin_url(self):
        super()._compute_access_url()
        for reservation in self:
            reservation.access_url = f"/my/reservations/precheckin/{reservation.id}"

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

    @api.depends("commission_percent", "price_total", "service_ids")
    def _compute_commission_amount(self):
        for reservation in self:
            if reservation.commission_percent > 0:
                reservation.commission_amount = (
                    reservation.price_total * reservation.commission_percent / 100
                )
                if reservation.service_ids:
                    for service in reservation.service_ids:
                        if service.is_board_service:
                            reservation.commission_amount = (
                                reservation.commission_amount
                                + service.price_total
                                * reservation.commission_percent
                                / 100
                            )
            else:
                reservation.commission_amount = 0

    # REVIEW: Dont run with set room_type_id -> room_id(compute)-> No set adults¿?
    @api.depends("preferred_room_id", "reservation_type", "overnight_room")
    def _compute_adults(self):
        for reservation in self:
            if not reservation.overnight_room:
                reservation.adults = 0
            if reservation.preferred_room_id and reservation.reservation_type != "out":
                if reservation.adults == 0:
                    reservation.adults = reservation.preferred_room_id.capacity
            elif not reservation.adults or reservation.reservation_type == "out":
                reservation.adults = 0

    @api.depends("reservation_line_ids", "reservation_line_ids.room_id")
    def _compute_splitted(self):
        # REVIEW: Updating preferred_room_id here avoids cyclical dependency
        for reservation in self:
            room_ids = reservation.reservation_line_ids.mapped("room_id.id")
            if len(room_ids) > 1 and not self._context.get("not_split"):
                reservation.splitted = True
                reservation.preferred_room_id = False
            else:
                reservation.splitted = False
                # Set automatically preferred_room_id if, and only if,
                # all nights has the same room
                if (
                    len(room_ids) == 1
                    and len(reservation.reservation_line_ids)
                    == (reservation.checkout - reservation.checkin).days
                ):
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
            if line.reservation_type not in ("normal", "staff"):
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
                        lambda x, r=record: x.reservation_id.id != r.id
                    )
                )
            else:
                record.shared_folio = False

    @api.depends(
        "partner_id",
        "partner_id.name",
        "agency_id",
        "reservation_type",
        "out_service_description",
        "folio_id.partner_name",
    )
    def _compute_partner_name(self):
        for record in self:
            if record.partner_id and record.partner_id != record.agency_id:
                record.partner_name = record.partner_id.name
            if (record.folio_id and not record.partner_name) or (
                record.folio_id.partner_name != record.partner_name
            ):
                record.partner_name = record.folio_id.partner_name
            elif record.agency_id and not record.partner_name:
                # if the customer not is the agency but we dont know the customer's
                # name, set the name provisional
                record.partner_name = _("Reservation from ") + record.agency_id.name
            elif not record.partner_name:
                record.partner_name = False

    @api.depends("partner_id", "partner_id.email", "agency_id")
    def _compute_email(self):
        for record in self:
            self.env["pms.folio"]._apply_email(record)

    @api.depends("partner_id", "partner_id.mobile", "agency_id")
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
            if record.reservation_type != "out" and record.overnight_room:
                occupancy = record.adults + record.children
                record.checkin_partner_count = len(record.checkin_partner_ids)
                record.checkin_partner_pending_count = occupancy - len(
                    record.checkin_partner_ids
                )
            else:
                record.checkin_partner_count = 0
                record.checkin_partner_pending_count = 0

    @api.depends("room_type_id", "partner_id")
    def _compute_tax_ids(self):
        for record in self:
            record = record.with_company(record.company_id)
            if (
                record.partner_id == record.company_id.partner_id
                and record.company_id.self_billed_tax_ids
            ):
                record.tax_ids = record.company_id.self_billed_tax_ids
            else:
                product = self.env["product.product"].browse(
                    record.room_type_id.product_id.id
                )
                record.tax_ids = product.taxes_id.filtered(
                    lambda t, r=record: t.company_id == r.env.company
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

    @api.depends("folio_id", "folio_id.reservation_type")
    def _compute_reservation_type(self):
        for record in self:
            if record.folio_id:
                record.reservation_type = record.folio_id.reservation_type
            else:
                record.reservation_type = "normal"

    @api.depends("email", "mobile", "partner_name")
    def _compute_possible_existing_customer_ids(self):
        for record in self:
            if record.partner_name:
                possible_customer = self.env[
                    "pms.folio"
                ]._apply_possible_existing_customer_ids(
                    record.email, record.mobile, record.partner_id
                )
                if possible_customer:
                    record.possible_existing_customer_ids = possible_customer
                else:
                    record.possible_existing_customer_ids = False
            else:
                record.possible_existing_customer_ids = False

    @api.depends("reservation_type")
    def _compute_avoid_mails(self):
        for record in self:
            if record.reservation_type == "out":
                record.avoid_mails = True
            elif not record.avoid_mails:
                record.avoid_mails = False

    @api.depends("reservation_type", "state")
    def _compute_to_send_confirmation_mail(self):
        for record in self:
            if record.state in ("confirm") and not record.avoid_mails:
                record.to_send_confirmation_mail = True
            else:
                record.to_send_confirmation_mail = False

    @api.depends("checkin", "checkout")
    def _compute_to_send_modification_mail(self):
        for record in self:
            if (
                record.state == "confirm"
                and not record.to_send_confirmation_mail
                and not record.avoid_mails
                and (
                    record._origin.checkin != record.checkin
                    or record._origin.checkout != record.checkout
                )
            ):
                record.to_send_modification_mail = True
            else:
                record.to_send_modification_mail = False

    @api.depends("reservation_type", "state")
    def _compute_to_send_exit_mail(self):
        for record in self:
            if record.state in ("done") and not record.avoid_mails:
                record.to_send_exit_mail = True
            else:
                record.to_send_exit_mail = False

    @api.depends("reservation_type", "state")
    def _compute_to_send_cancelation_mail(self):
        for record in self:
            if record.state in ("cancel") and not record.avoid_mails:
                record.to_send_cancelation_mail = True
            else:
                record.to_send_cancelation_mail = False

    @api.depends("partner_id")
    def _compute_lang(self):
        for record in self:
            if record.partner_id:
                record.lang = record.partner_id.lang
            else:
                record.lang = self.env["res.lang"].get_installed()

    @api.depends(
        "reservation_line_ids",
        "reservation_line_ids.sale_channel_id",
        "service_ids",
        "service_ids.sale_channel_origin_id",
    )
    def _compute_sale_channel_ids(self):
        for record in self:
            sale_channel_ids = []
            if record.reservation_line_ids:
                for sale in record.reservation_line_ids.mapped("sale_channel_id.id"):
                    sale_channel_ids.append(sale)
            if record.service_ids:
                for sale in record.service_ids.mapped("sale_channel_origin_id.id"):
                    sale_channel_ids.append(sale)
            sale_channel_ids = list(set(sale_channel_ids))
            record.sale_channel_ids = [(6, 0, sale_channel_ids)]

    @api.depends("agency_id")
    def _compute_sale_channel_origin_id(self):
        for record in self:
            if record.agency_id:
                record.sale_channel_origin_id = record.agency_id.sale_channel_id

    @api.depends("sale_channel_origin_id")
    def _compute_is_origin_channel_check_visible(self):
        for record in self:
            if (
                record.sale_channel_origin_id != record.folio_id.sale_channel_origin_id
                and record.folio_id
                # and isinstance(self.id, int)
                and record._origin.sale_channel_origin_id.id
            ):
                record.is_origin_channel_check_visible = True
            else:
                record.is_origin_channel_check_visible = False

    @api.depends("sale_channel_origin_id")
    def _compute_force_update_origin(self):
        for record in self:
            record.force_update_origin = True

    @api.depends("is_reselling")
    def _compute_is_reselling(self):
        for record in self:
            if any(record.reservation_line_ids.mapped("is_reselling")):
                record.is_reselling = True
            else:
                record.is_reselling = False

    @api.depends("reservation_line_ids")
    def _compute_count_alternative_free_rooms(self):
        for record in self:
            record.count_alternative_free_rooms = record.pms_property_id.with_context(
                checkin=record.checkin,
                checkout=record.checkout,
                real_avail=True,
                capacity=record.adults,
                class_id=record.room_type_id.class_id.id,
                current_lines=record.reservation_line_ids.ids,
            ).availability

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
            "|",
            ("adults", ">", 0),
            ("children", ">", 0),
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
            "|",
            ("adults", ">", 0),
            ("children", ">", 0),
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

    @api.depends("reservation_line_ids", "reservation_line_ids.overbooking")
    def _compute_overbooking(self):
        for record in self:
            record.overbooking = any(record.reservation_line_ids.mapped("overbooking"))

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

    def _get_default_sale_channel_origin(self):
        folio = False
        sale_channel_origin_id = False
        if "default_folio_id" in self._context:
            folio = self.env["pms.folio"].search(
                [("id", "=", self._context["default_folio_id"])]
            )
        if folio and folio.sale_channel_origin_id:
            sale_channel_origin_id = folio.sale_channel_origin_id
        return sale_channel_origin_id

    def check_in_out_dates(self):
        """
        1.-When date_order is less then checkin date or
        Checkout date should be greater than the checkin date.
        3.-Check the reservation dates are not occuped
        """
        for record in self:
            if record.checkout and record.checkin and record.checkin >= record.checkout:
                raise UserError(
                    _(
                        "Room line Check In Date Should be \
                    less than the Check Out Date!"
                    )
                )

    def _check_capacity(self):
        for record in self:
            if record.reservation_type != "out":
                self.env["pms.room"]._check_adults(
                    record, record.service_ids.service_line_ids
                )

    @api.constrains("reservation_line_ids")
    def checkin_checkout_consecutive_dates(self):
        """
        simply convert date objects to integers using the .toordinal() method
        of datetime objects. The difference between the maximum and minimum value
        of the set of ordinal dates is one more than the length of the set
        """
        for record in self:
            if min(record.reservation_line_ids.mapped("date")) != record.checkin:
                raise UserError(
                    _(
                        """
                        Compute error: The first room line date should
                        be the same as the checkin date!
                        """
                    )
                )
            if max(
                record.reservation_line_ids.mapped("date")
            ) != record.checkout - datetime.timedelta(days=1):
                raise UserError(
                    _(
                        """
                        Compute error: The last room line date should
                        be the previous day of the checkout date!
                        """
                    )
                )
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

    @api.constrains("state")
    def _check_onboard_reservation(self):
        for record in self:
            if (
                not record.checkin_partner_ids.filtered(lambda c: c.state == "onboard")
                and record.state == "onboard"
                and record.reservation_type != "out"
            ):
                raise ValidationError(
                    _("No person from reserve %s has arrived", record.name)
                )
            if record.state == "cancel" and not self.env.context.get("action_cancel"):
                raise ValidationError(
                    _("The reservation must be canceled by action: action_cancel")
                )
            if record.state == "confirm" and not self.env.context.get("action_confirm"):
                raise ValidationError(
                    _("The reservation must be confirmed by action: action_confirm")
                )

    @api.constrains("arrival_hour")
    def _check_arrival_hour(self):
        for record in self:
            if record.arrival_hour:
                try:
                    time.strptime(record.arrival_hour, "%H:%M")
                except ValueError as err:
                    raise ValidationError(
                        _("Format Arrival Hour (HH:MM) Error: %s", record.arrival_hour)
                    ) from err

    @api.constrains("departure_hour")
    def _check_departure_hour(self):
        for record in self:
            if record.departure_hour:
                try:
                    time.strptime(record.departure_hour, "%H:%M")
                except ValueError as err:
                    raise ValidationError(
                        _(
                            "Format Departure Hour (HH:MM) Error: %s",
                            record.departure_hour,
                        )
                    ) from err

    @api.constrains("agency_id")
    def _no_agency_as_agency(self):
        for record in self:
            if record.agency_id and not record.agency_id.is_agency:
                raise ValidationError(_("booking agency with wrong configuration: "))

    @api.constrains("closure_reason_id")
    def _check_closure_reason_id(self):
        for record in self:
            if record.reservation_type == "out":
                if not record.closure_reason_id:
                    raise ValidationError(
                        _(
                            "A closure reason is mandatory when reservation"
                            " type is 'out of service'"
                        )
                    )

    @api.constrains("reservation_type")
    def _check_same_reservation_type(self):
        for record in self:
            if len(record.folio_id.reservation_ids) > 1:
                for reservation in record.folio_id.reservation_ids:
                    if reservation.reservation_type != record.reservation_type:
                        raise ValidationError(
                            _(
                                "The reservation type must be the "
                                "same for all reservations in folio"
                            )
                        )

    @api.constrains(
        "reservation_line_ids", "reservation_line_ids.room_id", "room_type_id"
    )
    def _check_room_class_compatibility(self):
        for record in self:
            if (
                record.room_type_id
                and record.reservation_line_ids
                and all(line.room_id for line in record.reservation_line_ids)
            ):
                for line in record.reservation_line_ids:
                    if (
                        line.room_id.room_type_id.class_id
                        != record.room_type_id.class_id
                    ):
                        raise ValidationError(
                            _(
                                """The room %(room)s (type: %(room_type)s) is not
                                compatible with the room type %(record_room_type)s
                                (type: %(record_room_class)s)""",
                                room=line.room_id.name,
                                room_type=line.room_id.room_type_id.class_id.name,
                                record_room_type=record.room_type_id.name,
                                record_room_class=record.room_type_id.class_id.name,
                            )
                        )

    # Action methods
    def open_partner(self):
        """Utility method used to add an "View Customer" button in reservation views"""
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

    def action_open_confirmation_mail_composer(self):
        return self.folio_id.action_open_confirmation_mail_composer()

    def action_open_modification_mail_composer(self):
        return self.folio_id.action_open_modification_mail_composer()

    def action_open_exit_mail_composer(self):
        return self.folio_id.action_open_exit_mail_composer()

    def action_open_cancelation_mail_composer(self):
        return self.folio_id.action_open_cancelation_mail_composer()

    def open_wizard_several_partners(self):
        ctx = dict(
            reservation_id=self.id,
            possible_existing_customer_ids=self.possible_existing_customer_ids.ids,
        )
        return {
            "view_type": "form",
            "view_mode": "form",
            "name": "Several Customers",
            "res_model": "pms.several.partners.wizard",
            "target": "new",
            "type": "ir.actions.act_window",
            "context": ctx,
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
        return super().name_search(name="", args=args, operator="ilike", limit=limit)

    def name_get(self):
        result = []
        for res in self:
            name = "{} ({})".format(res.name, res.rooms if res.rooms else "No room")
            result.append((res.id, name))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("folio_id"):
                folio = self.env["pms.folio"].browse(vals["folio_id"])
                default_vals = {"pms_property_id": folio.pms_property_id.id}
                if folio.partner_id:
                    default_vals["partner_id"] = folio.partner_id.id
                elif folio.partner_name:
                    default_vals["partner_name"] = folio.partner_name
                    default_vals["mobile"] = folio.mobile
                    default_vals["email"] = folio.email
                elif vals.get("reservation_type") != "out":
                    raise ValidationError(_("Partner contact name is required"))
                if (
                    folio.sale_channel_origin_id
                    and "sale_channel_origin_id" not in vals
                ):
                    default_vals[
                        "sale_channel_origin_id"
                    ] = folio.sale_channel_origin_id.id
                vals.update(default_vals)
            elif (
                "pms_property_id" in vals
                and "sale_channel_origin_id" in vals
                and (
                    "partner_name" in vals
                    or "partner_id" in vals
                    or "agency_id" in vals
                )
            ):
                folio_vals = self._get_folio_vals(vals)

                self._check_clousure_reason(
                    reservation_type=vals.get("reservation_type"),
                    closure_reason_id=vals.get("closure_reason_id"),
                )

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
                raise ValidationError(
                    _(
                        "The Property and Sale Channel Origin are mandatory "
                        "in the reservation"
                    )
                )
            if vals.get("name", _("New")) == _("New") or "name" not in vals:
                folio_sequence = (
                    max(folio.mapped("reservation_ids.folio_sequence")) + 1
                    if folio.reservation_ids
                    else 1
                )
                vals["folio_sequence"] = folio_sequence
                vals["name"] = folio.name + "/" + str(folio_sequence)
            if not vals.get("reservation_type"):
                vals["reservation_type"] = (
                    folio.reservation_type if folio.reservation_type else "normal"
                )
            # Avoid send state field in vals, with the propouse to
            # use action_confirm or action_cancel methods
            reservation_state = False
            if "state" in vals:
                reservation_state = vals["state"]
                vals.pop("state")
        records = super().create(vals_list)
        for record in records:
            record._check_capacity()
            if (
                record.preconfirm and record.state == "draft"
            ) or reservation_state == "confirm":
                record.action_confirm()
            elif reservation_state == "cancel":
                record.action_cancel()

            record._check_services(vals)
            tourist_tax_services_cmds = record._compute_tourist_tax_lines()
            if tourist_tax_services_cmds:
                record.write(
                    {
                        "service_ids": tourist_tax_services_cmds,
                    }
                )
        return record

    def write(self, vals):
        if (
            any([record.blocked for record in self])
            and not self.env.context.get("force_write_blocked")
            and (
                "checkin" in vals
                or "checkout" in vals
                or "room_type_id" in vals
                or (
                    vals.get("reservation_line_ids")
                    and any(
                        [
                            (
                                "date" in line[2]
                                and (
                                    datetime.datetime.strptime(
                                        line[2]["date"], "%Y-%m-%d"
                                    ).date()
                                    != self.env["pms.reservation.line"]
                                    .browse(line[1])
                                    .date
                                )
                            )
                            or (
                                "price" in line[2]
                                and (
                                    round(line[2]["price"], 2)
                                    != round(
                                        self.env["pms.reservation.line"]
                                        .browse(line[1])
                                        .price,
                                        2,
                                    )
                                )
                            )
                            for line in vals.get("reservation_line_ids")
                            if line[0] == 1
                        ]
                    )
                )
            )
        ):
            raise ValidationError(_("Blocked reservations can't be modified"))
        folios_to_update_channel = self.env["pms.folio"]
        lines_to_update_channel = self.env["pms.reservation.line"]
        services_to_update_channel = self.env["pms.service"]
        if "sale_channel_origin_id" in vals:
            folios_to_update_channel = self.get_folios_to_update_channel(vals)
            lines_to_update_channel = self.get_lines_to_update_channel(vals)
            services_to_update_channel = self.get_services_to_update_channel(vals)
        res = super().write(vals)
        if folios_to_update_channel:
            folios_to_update_channel.sale_channel_origin_id = vals[
                "sale_channel_origin_id"
            ]
        if lines_to_update_channel:
            lines_to_update_channel.sale_channel_id = vals["sale_channel_origin_id"]
        if services_to_update_channel:
            services_to_update_channel.sale_channel_origin_id = vals[
                "sale_channel_origin_id"
            ]

        for record in self:
            record._check_services(vals)
            # Only check if adult to avoid to check capacity in intermediate states
            # (p.e. flush) that not take access to possible extra beds service in vals
            if "adults" in vals:
                record._check_capacity()
            if (
                "checkin" in vals
                or "checkout" in vals
                or "reservation_line_ids" in vals
            ):
                tourist_tax_services_cmds = record._compute_tourist_tax_lines()
                if tourist_tax_services_cmds:
                    record.write({"service_ids": tourist_tax_services_cmds})
        return res

    def _get_folio_vals(self, reservation_vals):
        folio_vals = {
            "pms_property_id": reservation_vals["pms_property_id"],
        }
        if reservation_vals.get("sale_channel_origin_id"):
            folio_vals["sale_channel_origin_id"] = reservation_vals.get(
                "sale_channel_origin_id"
            )
        if reservation_vals.get("partner_id"):
            folio_vals["partner_id"] = reservation_vals.get("partner_id")
        elif reservation_vals.get("agency_id"):
            folio_vals["agency_id"] = reservation_vals.get("agency_id")
        elif reservation_vals.get("partner_name"):
            folio_vals["partner_name"] = reservation_vals.get("partner_name")
            folio_vals["mobile"] = reservation_vals.get("mobile")
            folio_vals["email"] = reservation_vals.get("email")
        elif reservation_vals.get("reservation_type") != "out":
            raise ValidationError(_("Partner contact name is required"))
        if reservation_vals.get("reservation_type"):
            folio_vals["reservation_type"] = reservation_vals.get("reservation_type")
        return folio_vals

    def _check_clousure_reason(self, reservation_type, closure_reason_id):
        if reservation_type == "out" and not closure_reason_id:
            raise ValidationError(
                _(
                    "A closure reason is mandatory when reservation"
                    " type is 'out of service'"
                )
            )

    def _check_services(self, vals):
        # If we create a reservation with board service and other service at the
        # same time, compute_service_ids dont run (compute with readonly to False), and
        # we must force it to compute the services linked with the board service:
        if "board_service_room_id" in vals and "service_ids" in vals:
            self._compute_board_service_ids()

    def get_folios_to_update_channel(self, vals):
        folios_to_update_channel = self.env["pms.folio"]
        for folio in self.mapped("folio_id"):
            if (
                any(
                    res.sale_channel_origin_id == folio.sale_channel_origin_id
                    for res in self.filtered(lambda r, f=folio: r.folio_id == f)
                )
                and vals["sale_channel_origin_id"] != folio.sale_channel_origin_id.id
                and (
                    ("force_update_origin" in vals and vals.get("force_update_origin"))
                    or len(folio.reservation_ids) == 1
                )
            ):
                folios_to_update_channel += folio
        return folios_to_update_channel

    def get_lines_to_update_channel(self, vals):
        lines_to_update_channel = self.env["pms.reservation.line"]
        for record in self:
            for line in record.reservation_line_ids:
                if line.sale_channel_id == record.sale_channel_origin_id and (
                    vals["sale_channel_origin_id"] != line.sale_channel_id.id
                ):
                    lines_to_update_channel += line
        return lines_to_update_channel

    def get_services_to_update_channel(self, vals):
        services_to_update_channel = self.env["pms.service"]
        for record in self:
            for service in record.service_ids:
                if service.sale_channel_origin_id == record.sale_channel_origin_id and (
                    vals["sale_channel_origin_id"] != service.sale_channel_origin_id.id
                ):
                    services_to_update_channel += service
        return services_to_update_channel

    def update_prices(self):
        self.ensure_one()
        for line in self.reservation_line_ids:
            line.with_context(force_recompute=True)._compute_price()
        self.show_update_pricelist = False
        self.message_post(
            body=_(
                """Prices have been recomputed according to pricelist
                <b>%(pricelist)s</b> and room type <b>%(room_type)s</b>""",
                pricelist=self.pricelist_id.display_name,
                room_type=self.room_type_id.name,
            )
        )

    @api.model
    def autocheckout(self, reservation):
        reservation.action_reservation_checkout()
        if not any(
            [checkin.state == "done" for checkin in reservation.checkin_partner_ids]
        ):
            msg = _("No checkin was made for this reservation")
            reservation.message_post(
                subject=_("No Checkins!"), subtype="mt_comment", body=msg
            )
        return True

    def action_confirm(self):
        for record in self:
            vals = {}
            if record.checkin_partner_ids.filtered(lambda c: c.state == "onboard"):
                vals.update({"state": "onboard"})
            else:
                vals.update({"state": "confirm"})
            record.with_context(action_confirm=True).write(vals)
            record.reservation_line_ids.update({"cancel_discount": 0})
            # Unlink penalty service if exist
            record.service_ids.filtered(lambda s: s.is_cancel_penalty).unlink()
            if record.folio_id.state != "confirm":
                record.folio_id.action_confirm()
        return True

    def action_cancel(self):
        for record in self:
            # else state = cancel
            if not record.allowed_cancel:
                raise UserError(_("This reservation cannot be cancelled"))
            else:
                record.with_context(action_cancel=True).state = "cancel"
                record._check_cancel_penalty()
                record.cancel_datetime = fields.Datetime.now()
                # If all reservations in the folio are cancelled, cancel the folio
                if not (
                    record.folio_id.reservation_ids.filtered(
                        lambda r: r.state != "cancel"
                    )
                ):
                    record.folio_id.action_cancel()
                record.folio_id._compute_amount()

    def action_assign(self):
        for record in self:
            record.to_assign = False

    def _check_cancel_penalty(self):
        for record in self:
            # self.ensure_one()
            if record.state == "cancel":
                pricelist = record.pricelist_id
                if record._context.get("modified", False):
                    record.cancelled_reason = "modified"
                    _logger.info("Modified Reservation - No Penalty")
                    continue
                elif pricelist and pricelist.cancelation_rule_id:
                    rule = pricelist.cancelation_rule_id
                    tz_property = record.pms_property_id.tz
                    today = fields.Date.context_today(
                        record.with_context(tz=tz_property)
                    )
                    days_diff = (
                        fields.Date.from_string(record.checkin)
                        - fields.Date.from_string(today)
                    ).days
                    days = record.nights
                    if days_diff < 0:
                        record.cancelled_reason = "noshow"
                        penalty_percent = rule.penalty_noshow
                        if rule.apply_on_noshow == "first":
                            days = 1
                        elif rule.apply_on_noshow == "days":
                            days = rule.days_late - 1
                    elif days_diff < pricelist.cancelation_rule_id.days_intime:
                        record.cancelled_reason = "late"
                        penalty_percent = rule.penalty_late
                        if rule.apply_on_late == "first":
                            days = 1
                        elif rule.apply_on_late == "days":
                            days = rule.days_late
                    else:
                        record.cancelled_reason = "intime"
                        penalty_percent = 0
                        days = 0
                    # Generate a penalty service in the reservation
                    if penalty_percent:
                        dates = []
                        for i in range(0, days):
                            dates.append(
                                fields.Date.from_string(
                                    fields.Date.from_string(record.checkin)
                                    + datetime.timedelta(days=i)
                                )
                            )
                        amount_penalty = (
                            sum(
                                record.reservation_line_ids.filtered(
                                    lambda r, d=dates: fields.Date.from_string(r.date)
                                    in d
                                ).mapped("price")
                            )
                            * penalty_percent
                            / 100
                        )
                        if not amount_penalty:
                            return
                        if not record.company_id.cancel_penalty_product_id:
                            # Create a penalty product
                            record.company_id.cancel_penalty_product_id = self.env[
                                "product.product"
                            ].create(
                                {
                                    "name": _("Cancel Penalty"),
                                    "type": "service",
                                }
                            )
                        penalty_product = record.company_id.cancel_penalty_product_id
                        default_channel_id = (
                            self.env["pms.sale.channel"]
                            .search([("channel_type", "=", "direct")], limit=1)
                            .id,
                        )
                        self.env["pms.service"].create(
                            {
                                "product_id": penalty_product.id,
                                "folio_id": record.folio_id.id,
                                "reservation_id": record.id,
                                "name": penalty_product.name,
                                "sale_channel_origin_id": default_channel_id,
                                "service_line_ids": [
                                    (
                                        0,
                                        0,
                                        {
                                            "product_id": penalty_product.id,
                                            "day_qty": 1,
                                            "price_unit": amount_penalty,
                                            "date": fields.Date.today(),
                                        },
                                    )
                                ],
                            }
                        )
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

    def action_undo_onboard(self):
        for record in self:
            # Undo onboard all checkin partners:
            record.checkin_partner_ids.filtered(
                lambda check: check.state == "onboard"
            ).action_undo_onboard()
            record.action_confirm()
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
        reservations = self.env["pms.reservation"].search(
            [
                ("state", "in", ("draft", "confirm")),
                ("checkin", "<", fields.Date.today()),
                ("overnight_room", "=", True),
            ]
        )
        for reservation in reservations:
            reservation.state = "arrival_delayed"
            reservation.message_post(
                body=_(
                    """No entry has been recorded in this reservation""",
                )
            )

    @api.model
    def auto_departure_delayed(self):
        # No checkout when pass checkout hour
        reservations = self.env["pms.reservation"].search(
            [
                ("state", "in", ("onboard", "departure_delayed")),
                ("checkout", "<=", fields.Datetime.today().date()),
            ]
        )
        for reservation in reservations:
            if reservation.overnight_room:
                if reservation.checkout == fields.Datetime.today().date():
                    reservation.state = "departure_delayed"
                else:
                    reservation.autocheckout(reservation)
            else:
                reservation.state = "done"

    def preview_reservation(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "target": "self",
            "url": self.get_portal_url(),
        }

    def _compute_tourist_tax_lines(self):
        """Return ORM commands to sync tourist tax services on this reservation."""
        self.ensure_one()
        if self.reservation_type != "normal":
            return False
        tax_products = self._get_tourist_tax_products()
        if not tax_products:
            return []

        nightly_dates = self._get_nightly_dates()
        grouped_lines = self._build_grouped_tax_lines(tax_products, nightly_dates)
        existing_services = self._get_existing_tourist_tax_services()
        return self._build_service_commands(grouped_lines, existing_services)

    def _get_tourist_tax_products(self):
        return self.env["product.product"].search([("is_tourist_tax", "=", True)])

    def _get_nightly_dates(self):
        return [
            self.checkin + datetime.timedelta(days=i)
            for i in range((self.checkout - self.checkin).days)
        ]

    def _build_grouped_tax_lines(self, products, nightly_dates):
        grouped = {}
        for night_index, night_date in enumerate(nightly_dates):
            night_number = night_index + 1
            for product in products:
                if not self._should_apply_product_for_night(
                    product, night_date, night_number
                ):
                    continue

                quantity = (
                    self._get_applicable_guest_count(product)
                    if product.per_person
                    else 1
                )
                price_unit = self._get_product_price(product, quantity, night_date)
                key = (product.id, price_unit)

                line = {
                    "product_id": product.id,
                    "day_qty": quantity,
                    "price_unit": price_unit,
                    "date": night_date,
                }
                grouped.setdefault(key, []).append(line)
        return grouped

    def _should_apply_product_for_night(self, product, night_date, night_number):
        return (
            self._is_mmdd_in_range(
                night_date, product.tourist_tax_date_start, product.tourist_tax_date_end
            )
            and night_number >= product.tourist_tax_apply_from_night
            and (
                not product.tourist_tax_apply_to_night
                or night_number <= product.tourist_tax_apply_to_night
            )
        )

    def _get_applicable_guest_count(self, product):
        return len(
            self._get_guests_by_age(
                product.tourist_tax_min_age,
                product.tourist_tax_max_age,
            )
        )

    def _get_product_price(self, product, quantity, night_date):
        product = product.with_context(
            lang=self.partner_id.lang,
            property=self.pms_property_id.id,
        )
        pricelist = self.pricelist_id
        price = pricelist._get_product_price(
            product=product,
            partner=self.partner_id,
            quantity=quantity,
            consumption_date=night_date,
            uom=product.uom_id,
            pms_property_id=self.pms_property_id.id,
        )
        return self.env["account.tax"]._fix_tax_included_price_company(
            price,
            product.taxes_id,
            self.tax_ids,
            self.pms_property_id.company_id,
        )

    def _get_existing_tourist_tax_services(self):
        return self.service_ids.filtered(
            lambda s: s.product_id.product_tmpl_id.is_tourist_tax
        )

    def _build_service_commands(self, grouped_lines, existing_services):
        cmds = []
        existing_by_product = {s.product_id.id: s for s in existing_services}
        new_product_ids = {product_id for product_id, _ in grouped_lines}

        # Remove services no longer needed
        for product_id in existing_by_product.keys() - new_product_ids:
            cmds.append((2, existing_by_product[product_id].id))

        for (product_id, _price_unit), new_lines in grouped_lines.items():
            product = self.env["product.product"].browse(product_id)
            service = existing_by_product.get(product_id)

            if not service:
                cmds.append(
                    (
                        0,
                        0,
                        {
                            "reservation_id": self.id,
                            "folio_id": self.folio_id.id,
                            "product_id": product.id,
                            "name": product.name,
                            "per_day": True,
                            "service_line_ids": [(0, 0, line) for line in new_lines],
                        },
                    )
                )
            else:
                existing_lines = {line.date: line for line in service.service_line_ids}
                new_lines_by_date = {line["date"]: line for line in new_lines}
                line_cmds = []

                for date in existing_lines.keys() & new_lines_by_date.keys():
                    existing = existing_lines[date]
                    new = new_lines_by_date[date]
                    if (
                        existing.day_qty != new["day_qty"]
                        or existing.price_unit != new["price_unit"]
                    ):
                        line_cmds.append(
                            (
                                1,
                                existing.id,
                                {
                                    "day_qty": new["day_qty"],
                                    "price_unit": new["price_unit"],
                                },
                            )
                        )
                for date in existing_lines.keys() - new_lines_by_date.keys():
                    line_cmds.append((2, existing_lines[date].id))
                for date in new_lines_by_date.keys() - existing_lines.keys():
                    line_cmds.append((0, 0, new_lines_by_date[date]))

                if line_cmds:
                    cmds.append((1, service.id, {"service_line_ids": line_cmds}))

        return cmds

    def _get_guests_by_age(self, min_age=None, max_age=None):
        today = fields.Date.today()
        guests = self.checkin_partner_ids

        def age(birthdate):
            return (today - birthdate).days // 365 if birthdate else 0

        filtered = guests.filtered(
            lambda g: (
                (not min_age or age(g.birthdate_date) >= min_age)
                and (not max_age or age(g.birthdate_date) <= max_age)
            )
        )
        return filtered

    def _is_mmdd_in_range(self, check_date, start_mmdd, end_mmdd):
        """Check if a date falls between two MM-DD values,
        supporting wrap-around (e.g. Nov–Feb)."""
        if not start_mmdd or not end_mmdd:
            return True

        check_md = (check_date.month, check_date.day)
        start_md = tuple(map(int, start_mmdd.split("-")))
        end_md = tuple(map(int, end_mmdd.split("-")))

        if start_md <= end_md:
            return start_md <= check_md <= end_md
        else:
            return check_md >= start_md or check_md <= end_md

    def _render_invoice_note(self):
        self.ensure_one()
        template_str = self.pms_property_id.invoice_reservation_note_template or ""
        # `lang` puede venir del cliente o configurarse por defecto
        lang = self.partner_id.lang or self.env.user.lang
        rendered = (
            self.env["mail.render.mixin"]
            .with_context(lang=lang)
            ._render_template(template_str, "pms.reservation", self.ids)
        )
        return rendered.get(self.id, "")
