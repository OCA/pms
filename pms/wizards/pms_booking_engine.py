import datetime

from odoo import _, api, fields, models


class BookingEngine(models.TransientModel):
    _name = "pms.booking.engine"
    _description = "Booking engine"
    _check_pms_properties_auto = True

    start_date = fields.Date(
        string="From:",
        help="Start date for creation of reservations and folios",
        required=True,
    )
    end_date = fields.Date(
        string="To:",
        help="End date for creation of reservations and folios",
        required=True,
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
        string="Property",
        help="Property to which the folio belongs",
        default=lambda self: self._default_pms_property_id(),
        comodel_name="pms.property",
        check_pms_properties=True,
    )
    segmentation_ids = fields.Many2many(
        string="Segmentation",
        help="Partner Tags",
        ondelete="restrict",
        comodel_name="res.partner.category",
        domain="[('is_used_in_checkin', '=', True)]",
    )
    partner_name = fields.Char(
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
    folio_id = fields.Many2one(
        string="Folio",
        help="Folio in which are included new reservations",
        comodel_name="pms.folio",
        check_pms_properties=True,
    )
    availability_results = fields.One2many(
        help="Availability Results",
        readonly=False,
        store=True,
        comodel_name="pms.folio.availability.wizard",
        inverse_name="booking_engine_id",
        compute="_compute_availability_results",
        check_pms_properties=True,
    )
    reservation_type = fields.Selection(
        string="Type",
        help="The type of the reservation. "
        "Can be 'Normal', 'Staff' or 'Out of Service'",
        default=lambda *a: "normal",
        selection=[("normal", "Normal"), ("staff", "Staff"), ("out", "Out of Service")],
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
        required=True,
    )
    total_price_folio = fields.Float(
        string="Total Price",
        help="Total price of folio with taxes",
        compute="_compute_total_price_folio",
    )
    discount = fields.Float(
        help="Discount that be applied in total price",
        default=0,
    )
    can_create_folio = fields.Boolean(compute="_compute_can_create_folio")
    internal_comment = fields.Text(
        string="Internal Folio Notes",
        help="Internal Folio notes for Staff",
    )

    def _default_pms_property_id(self):
        if self._context.get("default_folio_id"):
            folio = self.env["pms.folio"].browse(self._context.get("default_folio_id"))
            return folio.pms_property_id.id
        else:
            return self.env.user.pms_property_id.id

    @api.depends("availability_results.rooms_selected_qty")
    def _compute_can_create_folio(self):
        for record in self:
            record.can_create_folio = any(
                record.availability_results.mapped("rooms_selected_qty")
            )

    @api.depends("partner_id")
    def _compute_pricelist_id(self):
        for record in self:
            record.pricelist_id = (
                record.partner_id.property_product_pricelist.id
                if record.partner_id.property_product_pricelist.is_pms_available
                else self.pms_property_id.default_pricelist_id.id
            )

    @api.depends("agency_id")
    def _compute_channel_type_id(self):
        for record in self:
            if record.agency_id:
                record.channel_type_id = record.agency_id.sale_channel_id.id

    @api.depends("availability_results.price_total", "discount")
    def _compute_total_price_folio(self):
        for record in self:
            record.total_price_folio = 0
            for line in record.availability_results:
                record.total_price_folio += line.price_total
            record.total_price_folio = record.total_price_folio * (1 - record.discount)

    @api.depends("agency_id")
    def _compute_partner_id(self):
        for record in self:
            if record.agency_id and record.agency_id.invoice_to_agency == "always":
                record.partner_id = record.agency_id.id
            elif not record.partner_id:
                record.partner_id = False

    @api.depends("partner_id", "agency_id")
    def _compute_partner_name(self):
        for record in self:
            if record.partner_id:
                record.partner_name = record.partner_id.name
            if (
                record.agency_id
                and not record.agency_id.invoice_to_agency == "always"
                and not record.partner_name
            ):
                record.partner_name = _("Reservation from ") + record.agency_id.name
            elif not record.partner_name:
                record.partner_name = False

    @api.depends(
        "start_date",
        "end_date",
        "pricelist_id",
    )
    def _compute_availability_results(self):
        for record in self:
            record.availability_results = False

            if record.start_date and record.end_date:
                if record.end_date == record.start_date:
                    record.end_date = record.end_date + datetime.timedelta(days=1)

                cmds = [(5, 0, 0)]

                for room_type_iterator in self.env["pms.room.type"].search(
                    [
                        "|",
                        ("pms_property_ids", "=", False),
                        ("pms_property_ids", "in", record.pms_property_id.id),
                    ]
                ):
                    pms_property = record.pms_property_id
                    pms_property = pms_property.with_context(
                        checkin=record.start_date,
                        checkout=record.end_date,
                        room_type_id=room_type_iterator.id,
                        pricelist_id=record.pricelist_id.id,
                    )
                    rooms_available_qty = pms_property.availability

                    cmds.append(
                        (
                            0,
                            0,
                            {
                                "booking_engine_id": record.id,
                                "checkin": record.start_date,
                                "checkout": record.end_date,
                                "room_type_id": room_type_iterator.id,
                                "rooms_available_qty": rooms_available_qty,
                            },
                        )
                    )
                    # remove old items
                    old_lines = record.availability_results.mapped("id")
                    for old_line in old_lines:
                        cmds.append((2, old_line))

                    record.availability_results = cmds

                    record.availability_results = record.availability_results.sorted(
                        key=lambda s: s.rooms_available_qty, reverse=True
                    )

    def create_folio(self):
        for record in self:
            if not record.folio_id:
                folio = self.env["pms.folio"].create(
                    {
                        "reservation_type": record.reservation_type,
                        "pricelist_id": record.pricelist_id.id,
                        "partner_id": record.partner_id.id
                        if record.partner_id
                        else False,
                        "partner_name": record.partner_name,
                        "pms_property_id": record.pms_property_id.id,
                        "agency_id": record.agency_id.id,
                        "sale_channel_origin_id": record.channel_type_id.id,
                        "segmentation_ids": [(6, 0, record.segmentation_ids.ids)],
                        "internal_comment": record.internal_comment,
                    }
                )
            else:
                folio = record.folio_id
            reservation_values = []
            for line in record.availability_results:
                for _reservations_to_create in range(0, line.rooms_selected_qty):
                    res_dict = {
                        "folio_id": folio.id,
                        "checkin": line.checkin,
                        "checkout": line.checkout,
                        "room_type_id": line.room_type_id.id,
                        "partner_id": record.partner_id.id
                        if record.partner_id
                        else False,
                        "partner_name": record.partner_name,
                        "pricelist_id": record.pricelist_id.id,
                        "pms_property_id": folio.pms_property_id.id,
                        "board_service_room_id": line.board_service_room_id.id,
                    }
                    reservation_values.append((0, 0, res_dict))
            folio.write(
                {
                    "reservation_ids": reservation_values,
                }
            )
            if record.discount:
                # TODO: Refact compute discount in reservation and service lines
                folio.reservation_ids.reservation_line_ids.discount = (
                    record.discount * 100
                )
            action = self.sudo().env.ref("pms.open_pms_folio1_form_tree_all").read()[0]
            action["views"] = [
                (self.sudo().env.ref("pms.pms_folio_view_form").id, "form")
            ]
            action["res_id"] = folio.id
            return action


class AvailabilityWizard(models.TransientModel):
    _name = "pms.folio.availability.wizard"
    _description = "Room type line in Booking Engine"
    _check_pms_properties_auto = True

    booking_engine_id = fields.Many2one(
        string="Folio Wizard ID",
        comodel_name="pms.booking.engine",
    )
    checkin = fields.Date(
        string="From:",
        help="Date Reservation starts ",
        required=True,
    )
    checkout = fields.Date(
        string="To:",
        help="Date Reservation ends",
        required=True,
    )
    room_type_id = fields.Many2one(
        string="Room Type",
        help="Room Type reserved",
        comodel_name="pms.room.type",
        check_pms_properties=True,
    )

    rooms_available_qty = fields.Integer(
        string="Available rooms",
        help="Number of rooms that are available",
        store=True,
        compute="_compute_rooms_available_qty",
    )
    rooms_selected_qty = fields.Integer(string="Number of Rooms Selected")
    price_per_room = fields.Float(
        string="Price per room",
        help="Price per room in folio",
        compute="_compute_price_per_room",
    )
    price_total = fields.Float(
        string="Total price",
        help="The total price in the folio",
        compute="_compute_price_total",
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Propertiy with access to the element;",
        related="booking_engine_id.pms_property_id",
    )
    board_service_room_id = fields.Many2one(
        string="Board Service",
        help="Board Service included in the room",
        comodel_name="pms.board.service.room.type",
        domain="""
            [
                ('pms_room_type_id','=',room_type_id),
                ('pms_property_id','=',pms_property_id)
            ]
        """,
        check_pms_properties=True,
    )

    @api.onchange("rooms_selected_qty")
    def onchange_rooms_selected_qty(self):
        for record in self:
            if record.rooms_selected_qty > record.rooms_available_qty:
                raise models.ValidationError(
                    _(
                        "The number of selected rooms ({selected_qty}) cannot be "
                        "greater than the number of available rooms ({available_qty})."
                    ).format(
                        selected_qty=record.rooms_selected_qty,
                        available_qty=record.rooms_available_qty,
                    )
                )

    @api.depends("room_type_id", "checkin", "checkout")
    def _compute_rooms_available_qty(self):
        for record in self:
            pms_property = record.booking_engine_id.pms_property_id
            pms_property = pms_property.with_context(
                checkin=record.checkin,
                checkout=record.checkout,
                room_type_id=record.room_type_id.id,
                pricelist_id=record.booking_engine_id.pricelist_id.id,
            )
            record.rooms_available_qty = pms_property.availability

    @api.depends("room_type_id", "board_service_room_id", "checkin", "checkout")
    def _compute_price_per_room(self):
        for record in self:
            record.price_per_room = self._get_price_by_room_type(
                room_type_id=record.room_type_id.id,
                board_service_room_id=record.board_service_room_id.id,
                checkin=record.checkin,
                checkout=record.checkout,
                pricelist_id=record.booking_engine_id.pricelist_id.id,
                pms_property_id=record.booking_engine_id.pms_property_id.id,
            )

    @api.depends("price_per_room", "rooms_selected_qty")
    def _compute_price_total(self):
        for record in self:
            record.price_total = record.price_per_room * record.rooms_selected_qty

    @api.model
    def _get_price_by_room_type(
        self,
        room_type_id,
        checkin,
        checkout,
        board_service_room_id,
        pricelist_id,
        pms_property_id,
        adults=False,
    ):
        if not room_type_id:
            return 0
        room_type_total_price_per_room = 0
        room_type = self.env["pms.room.type"].browse(room_type_id)
        pms_property = self.env["pms.property"].browse(pms_property_id)
        pricelist = self.env["product.pricelist"].browse(pricelist_id)

        product = room_type.product_id
        for date_iterator in [
            checkin + datetime.timedelta(days=x)
            for x in range(0, (checkout - checkin).days)
        ]:
            price = pricelist._get_product_price(
                product=product,
                quantity=1,
                consumption_date=date_iterator,
                pms_property_id=pms_property_id,
            )
            room_type_total_price_per_room += self.env[
                "account.tax"
            ]._fix_tax_included_price_company(
                price,
                product.taxes_id,
                product.taxes_id,  # Not exist service line, we repeat product taxes
                pms_property.company_id,
            )

        if board_service_room_id:
            board_service_room = self.env["pms.board.service.room.type"].browse(
                board_service_room_id
            )
            nights = (checkout - checkin).days
            adults = adults or room_type.get_room_type_capacity(pms_property_id)
            room_type_total_price_per_room += (
                board_service_room.amount * nights * adults
            )
        return room_type_total_price_per_room
