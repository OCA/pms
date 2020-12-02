# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import logging
import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, float_compare, float_is_zero

_logger = logging.getLogger(__name__)


class PmsReservation(models.Model):
    _name = "pms.reservation"
    _description = "Reservation"
    _inherit = ["mail.thread", "mail.activity.mixin", "portal.mixin"]
    _order = "priority desc, name"
    _check_company_auto = True

    # Default Methods ang Gets
    def _get_default_checkin(self):
        folio = False
        if "folio_id" in self._context:
            folio = self.env["pms.folio"].search(
                [("id", "=", self._context["folio_id"])]
            )
        if folio and folio.reservation_ids:
            return folio.reservation_ids[0].checkin
        else:
            return fields.Date.today()

    def _get_default_checkout(self):
        folio = False
        if "folio_id" in self._context:
            folio = self.env["pms.folio"].search(
                [("id", "=", self._context["folio_id"])]
            )
        if folio and folio.reservation_ids:
            return folio.reservation_ids[0].checkout
        else:
            return fields.Date.today() + datetime.timedelta(1)

    def _get_default_arrival_hour(self):
        folio = False
        # TODO: Change by property env variable (like company)
        default_arrival_hour = self.env.user.pms_property_id.default_arrival_hour
        if "folio_id" in self._context:
            folio = self.env["pms.folio"].search(
                [("id", "=", self._context["folio_id"])]
            )
        if folio and folio.reservation_ids:
            return folio.reservation_ids[0].arrival_hour
        else:
            return default_arrival_hour

    def _get_default_departure_hour(self):
        folio = False
        # TODO: Change by property env variable (like company)
        default_departure_hour = self.env.user.pms_property_id.default_departure_hour
        if "folio_id" in self._context:
            folio = self.env["pms.folio"].search(
                [("id", "=", self._context["folio_id"])]
            )
        if folio and folio.reservation_ids:
            return folio.reservation_ids[0].departure_hour
        else:
            return default_departure_hour

    @api.model
    def _get_default_pms_property(self):
        # TODO: Change by property env variable (like company)
        return self.env.user.pms_property_id

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

    @api.model
    def _default_diff_invoicing(self):
        """
        If the guest has an invoicing address set,
        this method return diff_invoicing = True, else, return False
        """
        if "reservation_id" in self.env.context:
            reservation = self.env["pms.reservation"].browse(
                [self.env.context["reservation_id"]]
            )
        if reservation.partner_id.id == reservation.partner_invoice_id.id:
            return False
        return True

    # Fields declaration
    name = fields.Text(
        "Reservation Description",
        compute="_compute_name",
        store=True,
        readonly=False,
        # required=True,
    )
    priority = fields.Integer(compute="_compute_priority", store="True", index=True)

    preferred_room_id = fields.Many2one(
        "pms.room",
        string="Room",
        tracking=True,
        ondelete="restrict",
        domain="[('id', 'in', allowed_room_ids)]",
    )
    allowed_room_ids = fields.Many2many(
        "pms.room",
        string="Allowed Rooms",
        compute="_compute_allowed_room_ids",
    )
    folio_id = fields.Many2one(
        "pms.folio",
        string="Folio",
        tracking=True,
        ondelete="restrict",
    )
    board_service_room_id = fields.Many2one(
        "pms.board.service.room.type",
        string="Board Service",
    )
    room_type_id = fields.Many2one(
        "pms.room.type",
        string="Room Type",
        tracking=True,
        # required=True,
        compute="_compute_room_type_id",
        store=True,
        readonly=False,
    )
    partner_id = fields.Many2one(
        "res.partner",
        tracking=True,
        ondelete="restrict",
        compute="_compute_partner_id",
        store=True,
        readonly=False,
    )
    agency_id = fields.Many2one(
        related="folio_id.agency_id",
        readonly=False,
        store=True,
    )
    channel_type_id = fields.Many2one(
        related="folio_id.channel_type_id",
        readonly=False,
        store=True,
    )
    partner_invoice_id = fields.Many2one(
        "res.partner",
        string="Invoice Address",
        help="Invoice address for current reservation.",
        compute="_compute_partner_invoice_id",
        store=True,
        readonly=False,
    )
    closure_reason_id = fields.Many2one(related="folio_id.closure_reason_id")
    company_id = fields.Many2one(
        related="folio_id.company_id", string="Company", store=True, readonly=True
    )
    pms_property_id = fields.Many2one(
        "pms.property",
        default=_get_default_pms_property,  # required=True
    )
    reservation_line_ids = fields.One2many(
        "pms.reservation.line",
        "reservation_id",
        compute="_compute_reservation_line_ids",
        store=True,
        readonly=False,
    )
    service_ids = fields.One2many(
        "pms.service",
        "reservation_id",
        compute="_compute_service_ids",
        store=True,
        readonly=False,
    )
    pricelist_id = fields.Many2one(
        "product.pricelist",
        string="Pricelist",
        ondelete="restrict",
        compute="_compute_pricelist_id",
        store=True,
        readonly=False,
    )
    commission_percent = fields.Float(
        string="Commission percent (%)",
        compute="_compute_commission_percent",
        store=True,
        readonly=False,
    )
    commission_amount = fields.Float(
        string="Commission amount",
        compute="_compute_commission_amount",
        store=True,
    )
    # TODO: Warning Mens to update pricelist
    checkin_partner_ids = fields.One2many(
        "pms.checkin.partner",
        "reservation_id",
        compute="_compute_checkin_partner_ids",
        store=True,
        readonly=False,
    )
    count_pending_arrival = fields.Integer(
        "Pending Arrival",
        compute="_compute_count_pending_arrival",
        store=True,
    )
    checkins_ratio = fields.Integer(
        string="Pending Arrival Ratio",
        compute="_compute_checkins_ratio",
    )
    pending_checkin_data = fields.Integer(
        "Checkin Data",
        compute="_compute_pending_checkin_data",
        store=True,
    )
    ratio_checkin_data = fields.Integer(
        string="Pending Checkin Data",
        compute="_compute_ratio_checkin_data",
    )
    ready_for_checkin = fields.Boolean(compute="_compute_ready_for_checkin")
    left_for_checkin = fields.Boolean(
        compute="_compute_left_for_checkin", search="_search_left_for_checkin"
    )
    checkin_today = fields.Boolean(
        compute="_compute_checkin_today", search="_search_checkin_today"
    )
    departure_today = fields.Boolean(
        compute="_compute_departure_today", search="_search_departure_today"
    )
    segmentation_ids = fields.Many2many(
        "res.partner.category",
        string="Segmentation",
        ondelete="restrict",
        default=_get_default_segmentation,
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="pricelist_id.currency_id",
        string="Currency",
        readonly=True,
    )
    tax_ids = fields.Many2many(
        "account.tax",
        string="Taxes",
        ondelete="restrict",
        domain=["|", ("active", "=", False), ("active", "=", True)],
    )
    move_line_ids = fields.Many2many(
        "account.move.line",
        "reservation_move_rel",
        "reservation_id",
        "move_line_id",
        string="Invoice Lines",
        copy=False,
    )
    analytic_tag_ids = fields.Many2many("account.analytic.tag", string="Analytic Tags")
    localizator = fields.Char(
        string="Localizator", compute="_compute_localizator", store=True
    )
    adults = fields.Integer(
        "Adults",
        tracking=True,
        help="List of adults there in guest list. ",
        compute="_compute_adults",
        store=True,
        readonly=False,
    )
    children_occupying = fields.Integer(
        string="Children occupying",
    )

    children = fields.Integer(
        "Children",
        readonly=False,
        tracking=True,
        help="Number of children there in guest list.",
    )
    to_assign = fields.Boolean("To Assign", tracking=True)
    state = fields.Selection(
        [
            ("draft", "Pre-reservation"),
            ("confirm", "Pending arrival"),
            ("onboard", "On Board"),
            ("done", "Out"),
            ("cancelled", "Cancelled"),
            ("no_show", "No Show"),
            ("no_checkout", "No Checkout"),
        ],
        string="Status",
        default=lambda *a: "draft",
        copy=False,
        index=True,
        tracking=True,
        readonly=True,
    )
    reservation_type = fields.Selection(
        related="folio_id.reservation_type", default=lambda *a: "normal"
    )
    splitted = fields.Boolean(
        "Splitted",
        compute="_compute_splitted",
        store=True,
    )

    rooms = fields.Char(string="Room/s", compute="_compute_rooms", store=True)

    credit_card_details = fields.Text(related="folio_id.credit_card_details")
    cancelled_reason = fields.Selection(
        [("late", "Late"), ("intime", "In time"), ("noshow", "No Show")],
        string="Cause of cancelled",
        tracking=True,
    )
    out_service_description = fields.Text("Cause of out of service")
    checkin = fields.Date("Check In", required=True, default=_get_default_checkin)
    checkout = fields.Date("Check Out", required=True, default=_get_default_checkout)
    arrival_hour = fields.Char(
        "Arrival Hour",
        default=_get_default_arrival_hour,
        help="Default Arrival Hour (HH:MM)",
    )
    departure_hour = fields.Char(
        "Departure Hour",
        default=_get_default_departure_hour,
        help="Default Departure Hour (HH:MM)",
    )
    checkin_datetime = fields.Datetime(
        "Exact Arrival",
        compute="_compute_checkin_datetime",
    )
    checkout_datetime = fields.Datetime(
        "Exact Departure",
        compute="_compute_checkout_datetime",
    )
    # TODO: As checkin_partner_count is a computed field, it can't not
    # be used in a domain filer Non-stored field
    # pms.reservation.checkin_partner_count cannot be searched
    # searching on a computed field can also be enabled by setting the
    # search parameter. The value is a method name returning a Domains
    checkin_partner_count = fields.Integer(
        "Checkin counter", compute="_compute_checkin_partner_count"
    )
    checkin_partner_pending_count = fields.Integer(
        "Checkin Pending Num",
        compute="_compute_checkin_partner_count",
        search="_search_checkin_partner_pending",
    )
    overbooking = fields.Boolean("Is Overbooking", default=False)
    reselling = fields.Boolean("Is Reselling", default=False)
    nights = fields.Integer("Nights", compute="_compute_nights", store=True)
    origin = fields.Char("Origin", compute="_compute_origin", store=True)
    detail_origin = fields.Char(
        "Detail Origin", compute="_compute_detail_origin", store=True
    )
    folio_pending_amount = fields.Monetary(related="folio_id.pending_amount")
    shared_folio = fields.Boolean(compute="_compute_shared")
    # Used to notify is the reservation folio has other reservations/services
    email = fields.Char("E-mail", related="partner_id.email")
    mobile = fields.Char("Mobile", related="partner_id.mobile")
    phone = fields.Char("Phone", related="partner_id.phone")
    partner_internal_comment = fields.Text(
        string="Internal Partner Notes", related="partner_id.comment"
    )
    folio_internal_comment = fields.Text(
        string="Internal Folio Notes", related="folio_id.internal_comment"
    )
    preconfirm = fields.Boolean("Auto confirm to Save", default=True)
    invoice_status = fields.Selection(
        [
            ("invoiced", "Fully Invoiced"),
            ("to invoice", "To Invoice"),
            ("no", "Nothing to Invoice"),
        ],
        string="Invoice Status",
        compute="_compute_invoice_status",
        store=True,
        readonly=True,
        default="no",
    )
    qty_to_invoice = fields.Float(
        compute="_compute_get_to_invoice_qty",
        string="To Invoice",
        store=True,
        readonly=True,
        digits=("Product Unit of Measure"),
    )
    qty_invoiced = fields.Float(
        compute="_compute_get_invoice_qty",
        string="Invoiced",
        store=True,
        readonly=True,
        digits=("Product Unit of Measure"),
    )
    price_subtotal = fields.Monetary(
        string="Subtotal",
        readonly=True,
        store=True,
        compute="_compute_amount_reservation",
    )
    price_total = fields.Monetary(
        string="Total",
        readonly=True,
        store=True,
        compute="_compute_amount_reservation",
    )
    price_tax = fields.Float(
        string="Taxes Amount",
        readonly=True,
        store=True,
        compute="_compute_amount_reservation",
    )
    price_services = fields.Monetary(
        string="Services Total",
        readonly=True,
        store=True,
        compute="_compute_amount_room_services",
    )
    price_room_services_set = fields.Monetary(
        string="Room Services Total",
        readonly=True,
        store=True,
        compute="_compute_amount_set",
    )
    discount = fields.Float(
        string="Discount (€)",
        digits=("Discount"),
        compute="_compute_discount",
        store=True,
    )

    # Compute and Search methods
    @api.depends("checkin", "checkout", "room_type_id")
    def _compute_name(self):
        for reservation in self:
            if (
                reservation.room_type_id
                and reservation.checkin
                and reservation.checkout
            ):
                checkin_str = reservation.checkin.strftime(DEFAULT_SERVER_DATE_FORMAT)
                checkout_str = reservation.checkout.strftime(DEFAULT_SERVER_DATE_FORMAT)
                reservation.name = (
                    reservation.room_type_id.name
                    + ": "
                    + checkin_str
                    + " - "
                    + checkout_str
                )
            else:
                reservation.name = "/"

    @api.depends("checkin")
    def _compute_priority(self):
        # TODO: Logic priority (100 by example)
        self.priority = 100

    @api.depends("preferred_room_id")
    def _compute_room_type_id(self):
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
        "reservation_line_ids.date", "overbooking", "state", "preferred_room_id"
    )
    def _compute_allowed_room_ids(self):
        for reservation in self:
            if reservation.checkin and reservation.checkout:
                if reservation.overbooking or reservation.state in ("cancelled"):
                    reservation.allowed_room_ids = self.env["pms.room"].search(
                        [("active", "=", True)]
                    )
                    return
                rooms_available = self.env[
                    "pms.room.type.availability"
                ].rooms_available(
                    checkin=reservation.checkin,
                    checkout=reservation.checkout,
                    room_type_id=False,  # Allow chosen any available room
                    current_lines=reservation.reservation_line_ids.ids,
                )
                reservation.allowed_room_ids = rooms_available

    @api.depends("reservation_type", "agency_id")
    def _compute_partner_id(self):
        for reservation in self:
            if reservation.reservation_type == "out":
                reservation.partner_id = reservation.pms_property_id.partner_id.id
            if reservation.folio_id:
                reservation.partner_id = reservation.folio_id.partner_id
            else:
                reservation.partner_id = False
            if not reservation.partner_id and reservation.agency_id:
                reservation.partner_id = reservation.agency_id

    @api.depends("partner_id")
    def _compute_partner_invoice_id(self):
        for reservation in self:
            if reservation.folio_id and reservation.folio_id.partner_id:
                addr = reservation.folio_id.partner_id.address_get(["invoice"])
            else:
                addr = reservation.partner_id.address_get(["invoice"])
            reservation.partner_invoice_id = addr["invoice"]

    @api.depends("checkin", "checkout")
    def _compute_reservation_line_ids(self):
        for reservation in self:
            cmds = []
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

    @api.depends("board_service_room_id")
    def _compute_service_ids(self):
        for reservation in self:
            board_services = []
            old_board_lines = reservation.service_ids.filtered_domain(
                [
                    ("is_board_service", "=", True),
                ]
            )
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

    @api.depends("partner_id")
    def _compute_pricelist_id(self):
        for reservation in self:
            if reservation.folio_id:
                pricelist_id = reservation.folio_id.pricelist_id.id
            else:
                pricelist_id = (
                    reservation.partner_id.property_product_pricelist
                    and reservation.partner_id.property_product_pricelist.id
                    or self.env.user.pms_property_id.default_pricelist_id.id
                )
            if reservation.pricelist_id.id != pricelist_id:
                # TODO: Warning change de pricelist?
                reservation.pricelist_id = pricelist_id

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
                    unassigned_checkins[i].sudo().unlink()
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
                reservation.with_context(
                    {"auto_create_checkin": True}
                ).checkin_partner_ids = checkins_lst

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
        for reservation in self.filtered(lambda r: r.adults > 0):
            reservation.ratio_checkin_data = (
                (reservation.adults - reservation.pending_checkin_data)
                * 100
                / reservation.adults
            )

    def _compute_left_for_checkin(self):
        # Reservations still pending entry today
        for record in self:
            record.left_for_checkin = (
                True
                if (
                    record.state in ["draft", "confirm", "no_show"]
                    and record.checkin <= fields.Date.today()
                )
                else False
            )

    def _search_left_for_checkin(self, operator, value):
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
            ("state", "in", ("draft", "confirm", "no_show")),
            ("checkin", "<=", today),
        ]

    def _compute_ready_for_checkin(self):
        # Reservations with hosts data enought to checkin
        for record in self:
            record.ready_for_checkin = (
                record.left_for_checkin
                and len(
                    record.checkin_partner_ids.filtered(
                        lambda c: c.state == "precheckin"
                    )
                )
                >= 1
            )

    def _compute_checkin_today(self):
        for record in self:
            record.checkin_today = (
                True if record.checkin == fields.Date.today() else False
            )
            # REVIEW: Late checkin?? (next day)

    def _search_checkin_today(self, operator, value):
        if operator not in ("=", "!="):
            raise UserError(_("Invalid domain operator %s", operator))

        if value not in (False, True):
            raise UserError(_("Invalid domain right operand %s", value))

        today = fields.Date.context_today(self)

        return [("checkin", operator, today)]

    def _compute_departure_today(self):
        for record in self:
            record.departure_today = (
                True if record.checkout == fields.Date.today() else False
            )

    def _search_departure_today(self, operator, value):
        if operator not in ("=", "!="):
            raise UserError(_("Invalid domain operator %s", operator))

        if value not in (False, True):
            raise UserError(_("Invalid domain right operand %s", value))

        searching_for_true = (operator == "=" and value) or (
            operator == "!=" and not value
        )
        today = fields.Date.context_today(self)

        return [("checkout", searching_for_true, today)]

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
                    reservation.price_total * reservation.commission_percent
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
        for reservation in self:
            if len(reservation.reservation_line_ids.mapped("room_id")) > 1:
                reservation.splitted = True
            else:
                reservation.splitted = False
                reservation.preferred_room_id = reservation.reservation_line_ids[
                    0
                ].room_id

    @api.depends("state", "qty_to_invoice", "qty_invoiced")
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a Reservation. Possible statuses:
        - no: if the Folio is not in status 'sale' or 'done', we consider
          that there is nothing to invoice. This is also hte default value
          if the conditions of no other status is met.
        - to invoice: we refer to the quantity to invoice of the line.
          Refer to method `_compute_get_to_invoice_qty()` for more information
          on how this quantity is calculated.
        - invoiced: the quantity invoiced is larger or equal to the
          quantity ordered.
        """
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        for line in self:
            if line.state == "draft":
                line.invoice_status = "no"
            elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                line.invoice_status = "to invoice"
            elif (
                float_compare(
                    line.qty_invoiced,
                    len(line.reservation_line_ids),
                    precision_digits=precision,
                )
                >= 0
            ):
                line.invoice_status = "invoiced"
            else:
                line.invoice_status = "no"

    @api.depends("qty_invoiced", "nights", "folio_id.state")
    def _compute_get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order,
        the quantity to invoice is calculated from the ordered quantity.
        Otherwise, the quantity delivered is used.
        """
        for line in self:
            if line.folio_id.state not in ["draft"]:
                line.qty_to_invoice = len(line.reservation_line_ids) - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    @api.depends("move_line_ids.move_id.state", "move_line_ids.quantity")
    def _compute_get_invoice_qty(self):
        """
        Compute the quantity invoiced. If case of a refund, the quantity
        invoiced is decreased. We must check day per day and sum or
        decreased on 1 unit per invoice_line
        """
        for line in self:
            qty_invoiced = 0.0
            for day in line.reservation_line_ids:
                invoice_lines = day.move_line_ids.filtered(
                    lambda r: r.move_id.state != "cancel"
                )
                qty_invoiced += len(
                    invoice_lines.filtered(lambda r: r.move_id.type == "out_invoice")
                ) - len(
                    invoice_lines.filtered(lambda r: r.move_id.type == "out_refund")
                )
            line.qty_invoiced = qty_invoiced

    @api.depends("reservation_line_ids")
    def _compute_nights(self):
        for res in self:
            res.nights = len(res.reservation_line_ids)

    @api.depends("folio_id", "checkin", "checkout")
    def _compute_localizator(self):
        # TODO: Compute localizator by reservation
        for record in self:
            record.localizator = fields.date.today()

    @api.depends("service_ids.price_total")
    def _compute_amount_room_services(self):
        for record in self:
            record.price_services = sum(record.mapped("service_ids.price_total"))

    @api.depends("price_services", "price_total")
    def _compute_amount_set(self):
        for record in self:
            record.price_room_services_set = record.price_services + record.price_total

    @api.depends(
        "reservation_line_ids.discount", "reservation_line_ids.cancel_discount"
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

    # TODO: Use default values on checkin /checkout is empty
    @api.constrains(
        "checkin", "checkout", "state", "preferred_room_id", "overbooking", "reselling"
    )
    def check_dates(self):
        """
        1.-When date_order is less then checkin date or
        Checkout date should be greater than the checkin date.
        3.-Check the reservation dates are not occuped
        """
        for record in self:
            if fields.Date.from_string(record.checkin) >= fields.Date.from_string(
                record.checkout
            ):
                raise ValidationError(
                    _(
                        "Room line Check In Date Should be \
                    less than the Check Out Date!"
                    )
                )

    @api.constrains("checkin_partner_ids", "adults")
    def _max_checkin_partner_ids(self):
        for record in self:
            if len(record.checkin_partner_ids) > record.adults:
                raise models.ValidationError(
                    _("The room already is completed (%s)", record.name)
                )

    @api.constrains("adults")
    def _check_adults(self):
        for record in self:
            extra_bed = record.service_ids.filtered(
                lambda r: r.product_id.is_extra_bed is True
            )
            for room in record.reservation_line_ids.room_id:
                if record.adults + record.children_occupying > room.get_capacity(
                    len(extra_bed)
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
            try:
                time.strptime(record.departure_hour, "%H:%M")
                return True
            except ValueError:
                raise ValidationError(
                    _("Format Departure Hour (HH:MM) Error: %s", record.departure_hour)
                )

    @api.constrains("agency_id")
    def _no_agency_as_agency(self):
        for record in self:
            if record.agency_id and not record.agency_id.is_agency:
                raise ValidationError(_("booking agency with wrong configuration: "))

    # @api.constrains("reservation_type", "partner_id")
    # def _check_partner_reservation(self):
    #     for reservation in self:
    #         if (
    #             reservation.reservation_type == "out"
    #             and reservation.partner_id.id != \
    #                   reservation.pms_property_id.partner_id.id
    #         ):
    #             raise models.ValidationError(
    #                 _("The partner on out reservations must be a property partner")
    #             )

    # @api.constrains("closure_reason_id", "reservation_type")
    # def _check_clousure_reservation(self):
    #     for reservation in self:
    #         if reservation.closure_reason_id and \
    #               reservation.reservation_type != "out":
    #             raise models.ValidationError(
    #                 _("Only the out reservations can has a clousure reason")
    #             )

    # self._compute_tax_ids() TODO: refact

    # Action methods

    def open_folio(self):
        action = self.env.ref("pms.open_pms_folio1_form_tree_all").read()[0]
        if self.folio_id:
            action["views"] = [(self.env.ref("pms.pms_folio_view_form").id, "form")]
            action["res_id"] = self.folio_id.id
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action

    def open_reservation_form(self):
        action = self.env.ref("pms.open_pms_reservation_form_tree_all").read()[0]
        action["views"] = [(self.env.ref("pms.pms_reservation_view_form").id, "form")]
        action["res_id"] = self.id
        return action

    def action_pay_folio(self):
        self.ensure_one()
        return self.folio_id.action_pay()

    def action_pay_reservation(self):
        self.ensure_one()
        partner = self.partner_id.id
        amount = min(self.price_room_services_set, self.folio_pending_amount)
        note = self.folio_id.name + " (" + self.name + ")"
        view_id = self.env.ref("pms.account_payment_view_form_folio").id
        return {
            "name": _("Register Payment"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "account.payment",
            "type": "ir.actions.act_window",
            "view_id": view_id,
            "context": {
                "default_folio_id": self.folio_id.id,
                "default_room_id": self.id,
                "default_amount": amount,
                "default_payment_type": "inbound",
                "default_partner_type": "customer",
                "default_partner_id": partner,
                "default_communication": note,
            },
            "target": "new",
        }

    def open_reservation_wizard(self):
        rooms_available = self.env["pms.room.type.availability"].rooms_available(
            checkin=self.checkin,
            checkout=self.checkout,
            current_lines=self.reservation_line_ids.ids,
        )
        # REVIEW: check capacity room
        return {
            "view_type": "form",
            "view_mode": "form",
            "name": "Unify the reservation",
            "res_model": "pms.reservation.wizard",
            "target": "new",
            "type": "ir.actions.act_window",
            "context": {
                "rooms_available": rooms_available.ids,
            },
        }

    # ORM Overrides
    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        if args is None:
            args = []
        if not (name == "" and operator == "ilike"):
            args += [
                "|",
                ("folio_id.name", operator, name),
                ("preferred_room_id.name", operator, name),
            ]
        return super(PmsReservation, self).name_search(
            name="", args=args, operator="ilike", limit=limit
        )

    def name_get(self):
        result = []
        for res in self:
            name = u"{} ({})".format(
                res.folio_id.name, res.rooms if res.rooms else "No room"
            )
            result.append((res.id, name))
        return result

    @api.model
    def create(self, vals):
        if "folio_id" in vals:
            folio = self.env["pms.folio"].browse(vals["folio_id"])
        elif "partner_id" in vals:
            folio_vals = {
                "partner_id": int(vals.get("partner_id")),
            }
            # Create the folio in case of need
            # (To allow to create reservations direct)
            folio = self.env["pms.folio"].create(folio_vals)
            vals.update(
                {
                    "folio_id": folio.id,
                    "reservation_type": vals.get("reservation_type"),
                }
            )
        record = super(PmsReservation, self).create(vals)
        if record.preconfirm:
            record.confirm()
        return record

    # Business methods

    def _compute_shared(self):
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

    def _autoassign(self):
        self.ensure_one()
        room_chosen = False
        rooms_available = self.env["pms.room.type.availability"].rooms_available(
            checkin=self.checkin,
            checkout=self.checkout,
            room_type_id=self.room_type_id.id or False,
        )
        if rooms_available:
            room_chosen = rooms_available[0]
        else:
            # We can split reserve night on multi rooms
            room_chosen = False
        return room_chosen

    @api.model
    def autocheckout(self):
        reservations = self.env["pms.reservation"].search(
            [
                ("state", "not in", ["done", "cancelled"]),
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

    def overbooking_button(self):
        self.ensure_one()
        self.overbooking = not self.overbooking

    def generate_copy_values(self, checkin=False, checkout=False):
        self.ensure_one()
        return {
            "name": self.name,
            "adults": self.adults,
            "children": self.children,
            "checkin": checkin or self.checkin,
            "checkout": checkout or self.checkout,
            "folio_id": self.folio_id.id,
            "state": self.state,
            "overbooking": self.overbooking,
            "reselling": self.reselling,
            "price_total": self.price_total,
            "price_tax": self.price_tax,
            "price_subtotal": self.price_subtotal,
            "splitted": self.splitted,
            "room_type_id": self.room_type_id.id,
            "preferred_room_id": self.preferred_room_id.id,
        }

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
            cancel_reason = (
                "intime"
                if self._context.get("no_penalty", False)
                else record.compute_cancelation_reason()
            )
            if self._context.get("no_penalty", False):
                _logger.info("Modified Reservation - No Penalty")
            record.write({"state": "cancelled", "cancelled_reason": cancel_reason})
            # record._compute_cancelled_discount()
            record.folio_id._compute_amount()

    def compute_cancelation_reason(self):
        self.ensure_one()
        pricelist = self.pricelist_id
        if pricelist and pricelist.cancelation_rule_id:
            tz_property = self.env.user.pms_property_id.tz
            today = fields.Date.context_today(self.with_context(tz=tz_property))
            days_diff = (
                fields.Date.from_string(self.checkin) - fields.Date.from_string(today)
            ).days
            if days_diff < 0:
                return "noshow"
            elif days_diff < pricelist.cancelation_rule_id.days_intime:
                return "late"
            else:
                return "intime"
        return False

    def draft(self):
        for record in self:
            record.state = "draft"
            record.reservation_line_ids.update({"cancel_discount": 0})

    # INFO: This function is not in use and should include `dto` in the search
    @api.model
    def get_reservations_dates(self, dfrom, dto, room_type=False):
        """
        @param self: The object pointer
        @param dfrom: range date from
        @param dto: range date to
        @return: dictionary of lists with reservations (a hash of arrays!)
                 with the reservations dates between dfrom and dto
        reservations_dates
            {'2018-07-30': [pms.reservation(29,), pms.reservation(30,),
                           pms.reservation(31,)],
             '2018-07-31': [pms.reservation(22,), pms.reservation(35,),
                           pms.reservation(36,)],
            }
        """
        domain = [("date", ">=", dfrom), ("date", "<", dto)]
        lines = self.env["pms.reservation.line"].search(domain)
        reservations_dates = {}
        for record in lines:
            reservations_dates.setdefault(record.date, []).append(
                [record.reservation_id, record.reservation_id.room_type_id]
            )
        return reservations_dates

    def _compute_checkin_partner_count(self):
        for record in self:
            if record.reservation_type != "out":
                record.checkin_partner_count = len(record.checkin_partner_ids)
                record.checkin_partner_pending_count = (
                    record.adults + record.children
                ) - len(record.checkin_partner_ids)
            else:
                record.checkin_partner_count = 0
                record.checkin_partner_pending_count = 0

    def _search_checkin_partner_pending(self, operator, value):
        self.ensure_one()
        recs = self.search([]).filtered(lambda x: x.checkin_partner_pending_count > 0)
        return [("id", "in", [x.id for x in recs])] if recs else []

    def action_reservation_checkout(self):
        for record in self:
            record.state = "done"
            if record.checkin_partner_ids:
                record.checkin_partner_ids.filtered(
                    lambda check: check.state == "onboard"
                ).action_done()
        return True

    def action_checks(self):
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
            "target": "new",
        }

    def action_onboard(self):
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
            "domain": [("reservation_id", "=", self.id)],
            "target": "new",
        }

    @api.model
    def auto_no_show(self):
        # No show when pass 1 day from checkin day
        no_show_reservations = self.env["pms.reservation"].search(
            [
                ("state", "in", ("draft", "confirm")),
                ("checkin", "<", fields.Date.today()),
            ]
        )
        no_show_reservations.state = "no_show"

    @api.model
    def auto_no_checkout(self):
        # No checkout when pass checkout hour
        reservations = self.env["pms.reservation"].search(
            [
                ("state", "in", ("onboard",)),
                ("checkout", "=", fields.Datetime.today()),
            ]
        )
        for reservation in reservations:
            if reservation.checkout_datetime <= fields.Datetime.now():
                reservations.state = "no_checkout"

    def unify(self):
        # TODO
        return True

    def _compute_tax_ids(self):
        for record in self:
            # If company_id is set, always filter taxes by the company
            folio = record.folio_id or self.env.context.get("default_folio_id")
            product = self.env["product.product"].browse(
                record.room_type_id.product_id.id
            )
            record.tax_ids = product.taxes_id.filtered(
                lambda r: not record.company_id or r.company_id == folio.company_id
            )

    @api.depends("reservation_line_ids", "reservation_line_ids.room_id")
    def _compute_rooms(self):
        self.rooms = False

        for reservation in self:
            if reservation.splitted:
                reservation.rooms = ", ".join(
                    [r for r in reservation.reservation_line_ids.mapped("room_id.name")]
                )
                reservation.preferred_room_id = False
            else:
                reservation.rooms = reservation.preferred_room_id.name
