import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class BookingDuplicate(models.TransientModel):
    _name = "pms.booking.duplicate"
    _description = "Duplicate Booking"
    _check_pms_properties_auto = True

    reference_folio_id = fields.Many2one(
        string="Folio Reference",
        help="Folio to copy data",
        comodel_name="pms.folio",
        check_pms_properties=True,
    )
    start_date = fields.Date(
        string="From:",
        help="Date from first copy Checkin (reference min checkin folio reservation)",
        required=True,
    )
    used_room_ids = fields.Many2many(
        string="Used Rooms",
        comodel_name="pms.room",
        compute="_compute_used_room_ids",
    )
    pricelist_id = fields.Many2one(
        string="Pricelist",
        help="Pricelist applied in folio",
        readonly=False,
        store=True,
        comodel_name="product.pricelist",
        compute="_compute_pricelist_id",
        check_pms_properties=True,
        domain="[('is_pms_available', '=', True)]",
    )
    pms_property_id = fields.Many2one(
        related="reference_folio_id.pms_property_id",
        string="Property",
        help="Property to which the folio belongs",
        comodel_name="pms.property",
        check_pms_properties=True,
    )
    segmentation_ids = fields.Many2many(
        string="Segmentation",
        help="Partner Tags",
        ondelete="restrict",
        comodel_name="res.partner.category",
        compute="_compute_segmentation_ids",
        store=True,
        readonly=False,
    )
    partner_name = fields.Char(
        string="Partner name",
        help="In whose name is the reservation",
        compute="_compute_partner_name",
        readonly=False,
        store=True,
    )
    partner_id = fields.Many2one(
        string="Partner",
        help="Partner who made the reservation",
        comodel_name="res.partner",
        compute="_compute_partner_id",
        readonly=False,
        store=True,
        check_pms_properties=True,
    )

    reservation_type = fields.Selection(
        string="Type",
        help="The type of the reservation. "
        "Can be 'Normal', 'Staff' or 'Out of Service'",
        selection=[("normal", "Normal"), ("staff", "Staff"), ("out", "Out of Service")],
        compute="_compute_reservation_type",
        readonly=False,
        store=True,
    )
    agency_id = fields.Many2one(
        string="Agency",
        help="Agency that made the reservation",
        comodel_name="res.partner",
        domain=[("is_agency", "=", True)],
        ondelete="restrict",
    )
    channel_type_id = fields.Many2one(
        string="Direct Sale Channel",
        help="Sales Channel through which the reservation was managed",
        readonly=False,
        store=True,
        comodel_name="pms.sale.channel",
        domain=[("channel_type", "=", "direct")],
        ondelete="restrict",
        compute="_compute_channel_type_id",
    )
    total_price_folio = fields.Float(
        string="Total Price",
        help="Total price of folio with taxes",
        compute="_compute_total_price_folio",
    )
    discount = fields.Float(
        string="Discount",
        help="Discount that be applied in total price",
        default=0,
    )
    internal_comment = fields.Text(
        string="Internal Folio Notes",
        help="Internal Folio notes for Staff",
    )
    created_folio_ids = fields.Many2many(
        string="Folios",
        help="Folios already created",
        comodel_name="pms.folio",
    )
    line_ids = fields.One2many(
        string="Rooms",
        help="Rooms to create",
        readonly=False,
        store=True,
        comodel_name="pms.reservation.duplicate",
        inverse_name="booking_duplicate_id",
        compute="_compute_line_ids",
        check_pms_properties=True,
    )
    recompute_prices = fields.Boolean(
        string="Recompute Price",
        help="""Leave unchecked if you want to respect
        the price of the original reservation regardless
        of what is marked in the rate""",
        default=False,
    )

    @api.depends("line_ids", "line_ids.preferred_room_id")
    def _compute_used_room_ids(self):
        for record in self:
            record.used_room_ids = record.line_ids.mapped("preferred_room_id.id")

    @api.depends("reference_folio_id")
    def _compute_pricelist_id(self):
        for record in self.filtered("reference_folio_id"):
            if not record.pricelist_id:
                record.pricelist_id = record.reference_folio_id.pricelist_id.id

    @api.depends("reference_folio_id", "agency_id")
    def _compute_channel_type_id(self):
        for record in self.filtered("reference_folio_id"):
            if record.reference_folio_id.agency_id == record.agency_id:
                record.channel_type_id = (
                    record.reference_folio_id.sale_channel_origin_id
                )
            elif record.agency_id:
                record.channel_type_id = record.agency_id.sale_channel_id.id

    @api.depends("reference_folio_id")
    def _compute_segmentation_ids(self):
        for record in self:
            record.segmentation_ids = record.reference_folio_id.segmentation_ids

    @api.depends("agency_id", "reference_folio_id")
    def _compute_partner_id(self):
        for record in self:
            if record.reference_folio_id.agency_id == record.agency_id:
                record.partner_id = record.reference_folio_id.partner_id
            elif record.agency_id and record.agency_id.invoice_to_agency == "always":
                record.partner_id = record.agency_id.id
            elif not record.partner_id:
                record.partner_id = False

    @api.depends("reference_folio_id")
    def _compute_reservation_type(self):
        self.reservation_type = "normal"
        for record in self:
            record.reservation_type = record.reference_folio_id.reservation_type

    @api.depends("partner_id")
    def _compute_partner_name(self):
        for record in self:
            if record.reference_folio_id.partner_id == record.partner_id:
                record.partner_name = record.reference_folio_id.partner_name
            elif record.partner_id:
                record.partner_name = record.partner_id.name
            if (
                record.agency_id
                and not record.agency_id.invoice_to_agency == "always"
                and not record.partner_name
            ):
                record.partner_name = _("Reservation from ") + record.agency_id.name
            elif not record.partner_name:
                record.partner_name = False

    @api.depends("line_ids.price_total")
    def _compute_total_price_folio(self):
        for record in self:
            record.total_price_folio = 0
            for line in record.line_ids:
                record.total_price_folio += line.price_total
            record.total_price_folio = record.total_price_folio

    @api.depends(
        "reference_folio_id",
    )
    def _compute_line_ids(self):
        self.ensure_one()
        reference_folio = self.reference_folio_id

        if not reference_folio:
            self.line_ids = False
            return

        cmds = [(5, 0)]

        for reservation in reference_folio.reservation_ids.filtered(
            lambda r: r.state != "cancel"
        ):
            cmds.append(
                (
                    0,
                    0,
                    {
                        "reference_reservation_id": reservation.id,
                        "booking_duplicate_id": self.id,
                        "checkin": False,
                        "checkout": False,
                        "preferred_room_id": reservation.preferred_room_id.id,
                        "room_type_id": reservation.room_type_id.id,
                        "pricelist_id": reservation.pricelist_id.id,
                        # "arrival_hour": reservation.arrival_hour,
                        # "departure_hour": reservation.departure_hour,
                        # "partner_internal_comment": reservation.partner_internal_comment,
                        "board_service_room_id": reservation.board_service_room_id.id,
                        "adults": reservation.adults,
                    },
                )
            )
        self.line_ids = cmds

    def create_and_new(self):
        self.create_folio()
        return {
            "name": _("Duplicate Folios"),
            "res_model": "pms.booking.duplicate",
            "type": "ir.actions.act_window",
            "view_id": self.env.ref("pms.booking_duplicate").id,
            "target": "new",
            "view_mode": "form",
            "context": {
                "default_reference_folio_id": self.reference_folio_id.id,
                "default_created_folio_ids": [(6, 0, self.created_folio_ids.ids)],
                "default_start_date": self.start_date,
            },
        }

    def create_and_close(self):
        self.create_folio()
        folio_ids = self.mapped("created_folio_ids.id")
        action = self.env.ref("pms.open_pms_folio1_form_tree_all").read()[0]
        if len(folio_ids) > 1:
            action["domain"] = [("id", "in", folio_ids)]
        elif len(folio_ids) == 1:
            form_view = [(self.env.ref("pms.pms_folio_view_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = folio_ids[0]
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action

    def view_folios(self):
        folio_ids = self.mapped("created_folio_ids.id")
        action = self.env.ref("pms.open_pms_folio1_form_tree_all").read()[0]
        if len(folio_ids) > 1:
            action["domain"] = [("id", "in", folio_ids)]
        elif len(folio_ids) == 1:
            form_view = [(self.env.ref("pms.pms_folio_view_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = folio_ids[0]
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action

    def create_folio(self):
        if any(room.occupied_room for room in self.line_ids):
            raise UserError(
                _(
                    """You can not create a new folio because there are rooms already occupied.
                    Please, check the rooms marked in red and try again."""
                )
            )
        folio = self.env["pms.folio"].create(
            {
                "reservation_type": self.reservation_type,
                "pricelist_id": self.pricelist_id.id,
                "partner_id": self.partner_id.id if self.partner_id else False,
                "partner_name": self.partner_name,
                "pms_property_id": self.pms_property_id.id,
                "agency_id": self.agency_id.id,
                "sale_channel_origin_id": self.channel_type_id.id,
                "segmentation_ids": [(6, 0, self.segmentation_ids.ids)],
                "internal_comment": self.internal_comment,
            }
        )
        for res in self.line_ids:
            displacement_days = (
                res.checkin - res.reference_reservation_id.checkin
            ).days
            res_vals = {
                "folio_id": folio.id,
                "checkin": res.checkin,
                "checkout": res.checkout,
                "room_type_id": res.room_type_id.id,
                "partner_id": self.partner_id.id if self.partner_id else False,
                "partner_name": self.partner_name,
                "pricelist_id": res.pricelist_id.id,
                "pms_property_id": folio.pms_property_id.id,
                "board_service_room_id": res.board_service_room_id.id,
                "adults": res.adults,
                "preferred_room_id": res.preferred_room_id.id,
            }
            ser_vals = [(5, 0)]
            for service in res.reference_reservation_id.service_ids.filtered(
                lambda s: not s.is_board_service
            ):
                ser_line_vals = [(5, 0)]
                if service.product_id.id in res.service_ids.ids:
                    for ser_line in service.service_line_ids:
                        ser_line_vals.append(
                            (
                                0,
                                0,
                                {
                                    "day_qty": ser_line.day_qty,
                                    "price_unit": ser_line.price_unit,
                                    "discount": ser_line.discount,
                                    "date": ser_line.date
                                    + datetime.timedelta(days=displacement_days)
                                    if service.per_day
                                    else fields.Date.today(),
                                },
                            )
                        )
                    ser_vals.append(
                        (
                            0,
                            0,
                            {
                                "product_id": service.product_id.id,
                                "is_board_service": service.is_board_service,
                                "service_line_ids": ser_line_vals,
                            },
                        )
                    )
            res_vals["service_ids"] = ser_vals

            if not self.recompute_prices:
                line_vals = [(5, 0)]
                for line in res.reference_reservation_id.reservation_line_ids:
                    line_vals.append(
                        (
                            0,
                            0,
                            {
                                "price": line.price,
                                "discount": line.discount,
                                "room_id": res.preferred_room_id.id,
                                "date": line.date
                                + datetime.timedelta(days=displacement_days),
                            },
                        )
                    )
                res_vals["reservation_line_ids"] = line_vals
            new_reservation = self.env["pms.reservation"].create(res_vals)
            # REVIEW: Board service overwrite prices
            for service in new_reservation.service_ids.filtered("is_board_service"):
                origin_services_board = (
                    res.reference_reservation_id.service_ids.filtered(
                        "is_board_service"
                    )
                )
                if origin_services_board:
                    service.service_line_ids.price_unit = (
                        origin_services_board.service_line_ids[0].price_unit
                    )
        self.created_folio_ids = [(4, folio.id)]


class PmsReservationDuplicate(models.TransientModel):
    _name = "pms.reservation.duplicate"
    _description = "Rooms in Duplicate Folio"
    _check_pms_properties_auto = True

    reference_reservation_id = fields.Many2one(
        string="Reservation Reference",
        help="Reservation to copy data",
        comodel_name="pms.reservation",
        check_pms_properties=True,
    )
    adults = fields.Integer(string="Adults")
    booking_duplicate_id = fields.Many2one(
        string="Folio Wizard ID",
        comodel_name="pms.booking.duplicate",
    )
    checkin = fields.Date(
        string="From:", help="Date Reservation starts ", compute="_compute_checkin"
    )
    checkout = fields.Date(
        string="To:",
        help="Date Reservation ends",
        compute="_compute_checkout",
    )
    room_type_id = fields.Many2one(
        string="Room Type",
        help="Room Type reserved",
        comodel_name="pms.room.type",
        check_pms_properties=True,
    )
    preferred_room_id = fields.Many2one(
        string="Room",
        help="Room reserved",
        comodel_name="pms.room",
        check_pms_properties=True,
        domain="["
        "('id', 'in', allowed_room_ids),"
        "('id', 'not in', used_room_ids),"
        "('pms_property_id', '=', pms_property_id),"
        "]",
    )
    used_room_ids = fields.Many2many(
        string="Used Rooms",
        comodel_name="pms.room",
        compute="_compute_used_room_ids",
    )
    allowed_room_ids = fields.Many2many(
        string="Allowed Rooms",
        help="It contains all available rooms for this reservation",
        comodel_name="pms.room",
        compute="_compute_allowed_room_ids",
    )
    occupied_room = fields.Boolean(
        string="Occupied Room",
        help="Check if the room is occupied",
        compute="_compute_occupied_room",
    )
    pricelist_id = fields.Many2one(
        string="Pricelist",
        help="Pricelist used for this reservation",
        comodel_name="product.pricelist",
        check_pms_properties=True,
        domain="[('is_pms_available', '=', True)]",
    )
    price_total = fields.Float(
        string="Total price",
        help="The total price in the folio",
        compute="_compute_price_total",
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Propertiy with access to the element;",
        related="booking_duplicate_id.pms_property_id",
    )
    board_service_room_id = fields.Many2one(
        string="Board Service",
        help="Board Service included in the room",
        comodel_name="pms.board.service.room.type",
        domain="[('pms_room_type_id','=',room_type_id)]",
        check_pms_properties=True,
    )
    service_ids = fields.Many2many(
        string="Services",
        comodel_name="product.product",
        relation="reservation_duplicate_product_rel",
        column1="reservation_duplicate_id",
        column2="product_id",
        compute="_compute_service_ids",
        readonly=False,
        store=True,
    )

    @api.depends("booking_duplicate_id.start_date")
    def _compute_checkin(self):
        self.checkin = False
        start_date = self.booking_duplicate_id.start_date
        if start_date:
            checkin_ref = min(
                self.booking_duplicate_id.mapped(
                    "reference_folio_id.reservation_ids.checkin"
                )
            )
            for record in self:
                if record.reference_reservation_id.checkin == checkin_ref:
                    record.checkin = start_date
                else:
                    dif_days = (
                        record.reference_reservation_id.checkin - checkin_ref
                    ).days
                    record.checkin = start_date + datetime.timedelta(days=dif_days)

    @api.depends("checkin")
    def _compute_checkout(self):
        self.checkout = False
        for record in self.filtered("checkin"):
            res_days = record.reference_reservation_id.nights
            record.checkout = record.checkin + datetime.timedelta(days=res_days)

    @api.depends(
        "checkin",
        "checkout",
        "preferred_room_id",
        "pms_property_id",
    )
    def _compute_allowed_room_ids(self):
        self.allowed_room_ids = False
        for reservation in self.filtered(lambda r: r.checkin and r.checkout):
            pms_property = reservation.pms_property_id
            pms_property = pms_property.with_context(
                checkin=reservation.checkin,
                checkout=reservation.checkout,
                room_type_id=False,  # Allows to choose any available room
                pricelist_id=reservation.pricelist_id.id,
                class_id=reservation.room_type_id.class_id.id
                if reservation.room_type_id
                else False,
                real_avail=True,
            )
            allowed_room_ids = pms_property.free_room_ids.ids
            reservation.allowed_room_ids = self.env["pms.room"].browse(allowed_room_ids)

    @api.depends("allowed_room_ids", "preferred_room_id")
    def _compute_occupied_room(self):
        self.occupied_room = False
        for record in self.filtered("preferred_room_id"):
            if (
                record.preferred_room_id.id not in record.allowed_room_ids.ids
                or record.preferred_room_id.id in record.used_room_ids.ids
            ):
                record.occupied_room = True

    @api.depends("preferred_room_id", "booking_duplicate_id.used_room_ids")
    def _compute_used_room_ids(self):
        self.used_room_ids = False
        for record in self:
            record.used_room_ids = list(
                set(record.booking_duplicate_id.used_room_ids.ids)
                - {record.preferred_room_id.id}
            )

    @api.depends("room_type_id", "board_service_room_id", "checkin", "checkout")
    def _compute_price_total(self):
        self.price_total = 0
        for record in self.filtered("checkout"):
            record.price_total = record.reference_reservation_id.price_room_services_set

    @api.depends("reference_reservation_id")
    def _compute_service_ids(self):
        for record in self:
            record.service_ids = list(
                set(record.reference_reservation_id.service_ids.mapped("product_id.id"))
            )
