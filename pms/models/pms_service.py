# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import _, api, fields, models


class PmsService(models.Model):
    _name = "pms.service"
    _description = "Services and its charges"
    _check_pms_properties_auto = True

    name = fields.Char(
        string="Service description",
        help="Service description",
        readonly=False,
        store=True,
        compute="_compute_name",
    )
    product_id = fields.Many2one(
        string="Service",
        help="Product associated with this service",
        required=True,
        comodel_name="product.product",
        ondelete="restrict",
        check_pms_properties=True,
        domain="[(is_pms_available, '=', True)]",
    )
    folio_id = fields.Many2one(
        string="Folio",
        help="Folio in which the service is included",
        readonly=False,
        store=True,
        comodel_name="pms.folio",
        compute="_compute_folio_id",
        check_pms_properties=True,
    )
    sale_line_ids = fields.One2many(
        string="Sale Lines",
        help="",
        copy=False,
        comodel_name="folio.sale.line",
        inverse_name="service_id",
        check_pms_properties=True,
    )
    reservation_id = fields.Many2one(
        string="Room",
        help="Reservation in which the service is included",
        default=lambda self: self._default_reservation_id(),
        comodel_name="pms.reservation",
        ondelete="cascade",
        check_pms_properties=True,
    )
    service_line_ids = fields.One2many(
        string="Service Lines",
        help="Subservices included in this service",
        readonly=False,
        store=True,
        comodel_name="pms.service.line",
        inverse_name="service_id",
        compute="_compute_service_line_ids",
        check_pms_properties=True,
    )
    company_id = fields.Many2one(
        string="Company",
        help="Company to which the service belongs",
        readonly=True,
        store=True,
        related="folio_id.company_id",
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Property to which the service belongs",
        readonly=True,
        store=True,
        comodel_name="pms.property",
        related="folio_id.pms_property_id",
        check_pms_properties=True,
    )
    tax_ids = fields.Many2many(
        string="Taxes",
        help="Taxes applied in the service",
        readonly=False,
        store=True,
        comodel_name="account.tax",
        domain=["|", ("active", "=", False), ("active", "=", True)],
        compute="_compute_tax_ids",
    )
    analytic_tag_ids = fields.Many2many(
        string="Analytic Tags",
        help="",
        comodel_name="account.analytic.tag",
    )
    currency_id = fields.Many2one(
        string="Currency",
        help="The currency used in relation to the folio",
        readonly=True,
        store=True,
        related="folio_id.currency_id",
    )
    sequence = fields.Integer(string="Sequence", help="", default=10)
    state = fields.Selection(
        string="State",
        help="Service status, it corresponds with folio status",
        related="folio_id.state",
        store=True,
    )
    per_day = fields.Boolean(
        string="Per Day",
        help="Indicates if service is sold by days",
        related="product_id.per_day",
        related_sudo=True,
    )
    product_qty = fields.Integer(
        string="Quantity",
        help="Number of services that were sold",
        readonly=False,
        store=True,
        compute="_compute_product_qty",
    )
    is_board_service = fields.Boolean(
        string="Is Board Service",
        help="Indicates if the service is part of a board service",
    )
    # Non-stored related field to allow portal user to
    # see the image of the product he has ordered
    product_image = fields.Binary(
        string="Product Image",
        help="Image of the service",
        store=False,
        related="product_id.image_1024",
        related_sudo=True,
    )
    invoice_status = fields.Selection(
        string="Invoice Status",
        help="State in which the service is with respect to invoices."
        "It can be 'invoiced', 'to_invoice' or 'no'",
        readonly=True,
        default="no",
        store=True,
        compute="_compute_invoice_status",
        selection=[
            ("invoiced", "Fully Invoiced"),
            ("to_invoice", "To Invoice"),
            ("no", "Nothing to Invoice"),
        ],
    )
    sale_channel_origin_id = fields.Many2one(
        string="Sale Channel Origin",
        help="Sale Channel through which service was created, the original",
        comodel_name="pms.sale.channel",
        check_pms_properties=True,
    )
    price_subtotal = fields.Monetary(
        string="Subtotal",
        help="Subtotal price without taxes",
        readonly=True,
        store=True,
        compute="_compute_amount_service",
    )
    price_total = fields.Monetary(
        string="Total",
        help="Total price with taxes",
        readonly=True,
        store=True,
        compute="_compute_amount_service",
    )
    price_tax = fields.Float(
        string="Taxes Amount",
        help="Total of taxes in service",
        readonly=True,
        store=True,
        compute="_compute_amount_service",
    )

    discount = fields.Float(
        string="Discount (€/ud)",
        help="Discount of total price",
        readonly=False,
        store=True,
        digits=("Discount"),
        compute="_compute_discount",
        inverse="_inverse_discount",
    )
    no_auto_add_lines = fields.Boolean(
        string="Force No Auto Add Lines",
        help="""Technical field to avoid add service lines to service
        automatically when creating a new service. It is used when
        creating a new service with lines in vals
        """,
        default=False,
    )
    default_invoice_to = fields.Many2one(
        string="Invoice to",
        help="""Indicates the contact to which this line will be
        billed by default, if it is not established,
        a guest or the generic contact will be used instead""",
        readonly=False,
        store=True,
        compute="_compute_default_invoice_to",
        comodel_name="res.partner",
        ondelete="restrict",
    )

    # Compute and Search methods
    @api.depends("product_id")
    def _compute_tax_ids(self):
        for service in self:
            service.tax_ids = service.product_id.taxes_id.filtered(
                lambda r: not service.company_id or r.company_id == service.company_id
            )

    @api.depends("service_line_ids", "service_line_ids.day_qty")
    def _compute_product_qty(self):
        self.product_qty = 0
        for service in self.filtered("service_line_ids"):
            qty = sum(service.service_line_ids.mapped("day_qty"))
            service.product_qty = qty

    @api.depends("reservation_id", "reservation_id.folio_id")
    def _compute_folio_id(self):
        for record in self:
            if record.reservation_id:
                record.folio_id = record.reservation_id.folio_id
            elif not record.folio_id:
                record.folio_id = False

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

    @api.depends("service_line_ids.price_day_total")
    def _compute_amount_service(self):
        for service in self:
            if service.service_line_ids:
                service.update(
                    {
                        "price_tax": sum(
                            service.service_line_ids.mapped("price_day_tax")
                        ),
                        "price_total": sum(
                            service.service_line_ids.mapped("price_day_total")
                        ),
                        "price_subtotal": sum(
                            service.service_line_ids.mapped("price_day_subtotal")
                        ),
                    }
                )
            else:
                service.update(
                    {
                        "price_tax": 0,
                        "price_total": 0,
                        "price_subtotal": 0,
                    }
                )

    @api.depends("product_id")
    def _compute_name(self):
        self.name = False
        for service in self.filtered("product_id"):
            product = service.product_id.with_context(
                lang=service.folio_id.partner_id.lang,
                partner=service.folio_id.partner_id.id,
            )
            title = False
            message = False
            warning = {}
            if product.sale_line_warn != "no-message":
                title = _("Warning for %s") % product.name
                message = product.sale_line_warn_msg
                warning["title"] = title
                warning["message"] = message
                result = {"warning": warning}
                if product.sale_line_warn == "block":
                    self.product_id = False
                    return result
            name = product.name_get()[0][1]
            if product.description_sale:
                name += "\n" + product.description_sale
            service.name = name

    @api.depends(
        "reservation_id.reservation_line_ids",
        "product_id",
        "reservation_id.adults",
    )
    def _compute_service_line_ids(self):
        for service in self:
            if service.no_auto_add_lines:
                continue
            if service.product_id:
                day_qty = 1
                if service.reservation_id and service.product_id:
                    reservation = service.reservation_id
                    # REVIEW: review method dependencies, reservation_line_ids
                    #         instead of checkin/checkout
                    if not reservation.checkin or not reservation.checkout:
                        if not service.service_line_ids:
                            service.service_line_ids = False
                        continue
                    product = service.product_id
                    consumed_on = product.consumed_on
                    if product.per_day:
                        lines = []
                        day_qty = service._service_day_qty()
                        days_diff = (reservation.checkout - reservation.checkin).days
                        for i in range(0, days_diff):
                            if consumed_on == "after":
                                i += 1
                            idate = reservation.checkin + timedelta(days=i)
                            old_line = service.service_line_ids.filtered(
                                lambda r: r.date == idate
                            )
                            price_unit = service._get_price_unit_line(idate)
                            if old_line and old_line.auto_qty:
                                lines.append(
                                    (
                                        1,
                                        old_line.id,
                                        {
                                            "day_qty": day_qty,
                                            "auto_qty": True,
                                        },
                                    )
                                )
                            elif not old_line:
                                lines.append(
                                    (
                                        0,
                                        False,
                                        {
                                            "date": idate,
                                            "day_qty": day_qty,
                                            "auto_qty": True,
                                            "price_unit": price_unit,
                                        },
                                    )
                                )
                        move_day = 0
                        if consumed_on == "after":
                            move_day = 1
                        for del_service_id in service.service_line_ids.filtered_domain(
                            [
                                "|",
                                (
                                    "date",
                                    "<",
                                    reservation.checkin + timedelta(move_day),
                                ),
                                (
                                    "date",
                                    ">=",
                                    reservation.checkout + timedelta(move_day),
                                ),
                            ]
                        ).ids:
                            lines.append((2, del_service_id))
                        # TODO: check intermediate states in check_adults restriction
                        #   when lines are removed
                        service.service_line_ids = lines
                    else:
                        if not service.service_line_ids:
                            price_unit = service._get_price_unit_line()
                            service.service_line_ids = [
                                (
                                    0,
                                    False,
                                    {
                                        "date": fields.Date.today(),
                                        "day_qty": day_qty,
                                        "price_unit": price_unit,
                                    },
                                )
                            ]
                else:
                    if not service.service_line_ids:
                        price_unit = service._get_price_unit_line()
                        service.service_line_ids = [
                            (
                                0,
                                False,
                                {
                                    "date": fields.Date.today(),
                                    "day_qty": day_qty,
                                    "price_unit": price_unit,
                                },
                            )
                        ]
            else:
                service.service_line_ids = False

    @api.depends("service_line_ids.cancel_discount")
    def _compute_discount(self):
        for record in self:
            discount = 0
            for line in record.service_line_ids:
                amount = line.day_qty * line.price_unit
                first_discount = amount * ((line.discount or 0.0) * 0.01)
                price = amount - first_discount
                cancel_discount = price * ((line.cancel_discount or 0.0) * 0.01)
                discount += first_discount + cancel_discount
            record.discount = discount

    def _inverse_discount(self):
        # compute the discount line percentage
        # based on the discount amount
        for record in self:
            for line in record.service_line_ids:
                line.discount = record.discount
                line.cancel_discount = 0

    @api.depends("sale_channel_origin_id", "folio_id.agency_id")
    def _compute_default_invoice_to(self):
        for record in self:
            agency = record.folio_id.agency_id
            if (
                agency
                and agency.invoice_to_agency == "always"
                and agency.sale_channel_id == record.sale_channel_origin_id
            ):
                record.default_invoice_to = agency
            elif not record.default_invoice_to:
                record.default_invoice_to = False

    def name_get(self):
        result = []
        for rec in self:
            name = []
            name.append("{name}".format(name=rec.name))
            if rec.reservation_id.name:
                name.append("{name}".format(name=rec.reservation_id.name))
            result.append((rec.id, ", ".join(name)))
        return result

    @api.model
    def _default_reservation_id(self):
        if self.env.context.get("reservation_ids"):
            ids = [item[1] for item in self.env.context["reservation_ids"]]
            return self.env["pms.reservation"].browse([(ids)], limit=1)
        elif self.env.context.get("default_reservation_id"):
            return self.env.context.get("default_reservation_id")
        return False

    # Action methods
    def open_service_ids(self):
        action = self.env.ref("pms.action_pms_services_form").sudo().read()[0]
        action["views"] = [(self.env.ref("pms.pms_service_view_form").id, "form")]
        action["res_id"] = self.id
        action["target"] = "new"
        return action

    # ORM Overrides
    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        if args is None:
            args = []
        if not (name == "" and operator == "ilike"):
            args += [
                "|",
                ("reservation_id.name", operator, name),
                ("name", operator, name),
            ]
        return super(PmsService, self).name_search(
            name="", args=args, operator="ilike", limit=limit
        )

    def _get_display_price(self, product):
        folio = self.folio_id
        reservation = self.reservation_id
        origin = folio if folio else reservation
        return self.env["product.product"]._pms_display_price(
            pricelist_id=origin.pricelist_id.id,
            product_id=product.id,
            company_id=origin.company_id.id,
            product_qty=self.product_qty or 1.0,
            partner_id=origin.partner_id.id if origin.partner_id else False,
        )

    # Businness Methods
    def _service_day_qty(self):
        self.ensure_one()
        qty = self.product_qty if len(self.service_line_ids) == 1 else 1
        if not self.reservation_id:
            return qty
        # TODO: Pass per_person to service line from product default_per_person
        #   When the user modifies the quantity avoid overwriting
        if self.product_id.per_person:
            qty = self.reservation_id.adults
        return qty

    def _get_price_unit_line(self, date=False):
        self.ensure_one()
        if self.reservation_id.reservation_type == "normal":
            folio = self.folio_id
            reservation = self.reservation_id
            origin = reservation if reservation else folio
            if origin:
                partner = origin.partner_id
                pricelist = origin.pricelist_id
                board_room_type = False
                product_context = dict(
                    self.env.context,
                    lang=partner.lang,
                    partner=partner.id,
                    quantity=self.product_qty,
                    date=folio.date_order if folio else fields.Date.today(),
                    pricelist=pricelist.id,
                    board_service=board_room_type.id if board_room_type else False,
                    uom=self.product_id.uom_id.id,
                    fiscal_position=False,
                    property=origin.pms_property_id.id,
                )
                if date:
                    product_context["consumption_date"] = date
                if reservation and self.is_board_service:
                    product_context[
                        "board_service"
                    ] = reservation.board_service_room_id.id
                product = self.product_id.with_context(product_context)
                return self.env["account.tax"]._fix_tax_included_price_company(
                    self.env["product.product"]._pms_get_display_price(
                        pricelist_id=pricelist.id,
                        product=product,
                        company_id=origin.company_id.id,
                        product_qty=self.product_qty,
                        partner_id=partner.id,
                    ),
                    product.taxes_id,
                    self.tax_ids,
                    origin.company_id,
                )
            else:
                return 0

    @api.model
    def create(self, vals):
        if vals.get("reservation_id") and not vals.get("sale_channel_origin_id"):
            reservation = self.env["pms.reservation"].browse(vals["reservation_id"])
            if reservation.sale_channel_origin_id:
                vals["sale_channel_origin_id"] = reservation.sale_channel_origin_id.id
        elif (
            vals.get("folio_id")
            and not vals.get("reservation_id")
            and not vals.get("sale_channel_origin_id")
        ):
            folio = self.env["pms.folio"].browse(vals["folio_id"])
            if folio.sale_channel_origin_id:
                vals["sale_channel_origin_id"] = folio.sale_channel_origin_id.id
        record = super(PmsService, self).create(vals)
        return record

    def write(self, vals):
        folios_to_update_channel = self.env["pms.folio"]
        lines_to_update_channel = self.env["pms.service.line"]
        if "sale_channel_origin_id" in vals:
            folios_to_update_channel = self.get_folios_to_update_channel(vals)
        res = super(PmsService, self).write(vals)
        if folios_to_update_channel:
            folios_to_update_channel.sale_channel_origin_id = vals[
                "sale_channel_origin_id"
            ]
        if lines_to_update_channel:
            lines_to_update_channel.sale_channel_id = vals["sale_channel_origin_id"]
        return res

    def get_folios_to_update_channel(self, vals):
        folios_to_update_channel = self.env["pms.folio"]
        for folio in self.mapped("folio_id"):
            if (
                any(
                    service.sale_channel_origin_id == folio.sale_channel_origin_id
                    for service in self.filtered(lambda r: r.folio_id == folio)
                )
                and vals["sale_channel_origin_id"] != folio.sale_channel_origin_id.id
                and (len(folio.reservation_ids) == 0)
                and (len(folio.service_ids) == 1)
            ):
                folios_to_update_channel += folio
        return folios_to_update_channel
