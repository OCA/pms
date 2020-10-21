# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.tools import float_compare, float_is_zero

_logger = logging.getLogger(__name__)


class PmsService(models.Model):
    _name = "pms.service"
    _description = "Services and its charges"

    # Default methods

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

    @api.model
    def _default_folio_id(self):
        if "folio_id" in self._context:
            return self._context["folio_id"]
        return False

    # Fields declaration
    name = fields.Char(
        "Service description",
        compute="_compute_name",
        store=True,
        readonly=False,
    )
    product_id = fields.Many2one(
        "product.product", "Service", ondelete="restrict", required=True
    )
    folio_id = fields.Many2one(
        "pms.folio", "Folio", ondelete="cascade", default=_default_folio_id
    )
    reservation_id = fields.Many2one(
        "pms.reservation", "Room", default=_default_reservation_id
    )
    service_line_ids = fields.One2many(
        "pms.service.line",
        "service_id",
        compute="_compute_service_line_ids",
        store=True,
        readonly=False,
    )
    company_id = fields.Many2one(
        related="folio_id.company_id", string="Company", store=True, readonly=True
    )
    pms_property_id = fields.Many2one(
        "pms.property", store=True, readonly=True, related="folio_id.pms_property_id"
    )
    tax_ids = fields.Many2many(
        "account.tax",
        string="Taxes",
        compute="_compute_tax_ids",
        store=True,
        readonly=False,
        domain=["|", ("active", "=", False), ("active", "=", True)],
    )
    move_line_ids = fields.Many2many(
        "account.move.line",
        "service_line_move_rel",
        "service_id",
        "move_line_id",
        string="move Lines",
        copy=False,
    )
    analytic_tag_ids = fields.Many2many("account.analytic.tag", string="Analytic Tags")
    currency_id = fields.Many2one(
        related="folio_id.currency_id", store=True, string="Currency", readonly=True
    )
    sequence = fields.Integer(string="Sequence", default=10)
    state = fields.Selection(related="folio_id.state")
    per_day = fields.Boolean(related="product_id.per_day", related_sudo=True)
    product_qty = fields.Integer(
        "Quantity",
        compute="_compute_product_qty",
        store=True,
        readonly=False,
    )
    is_board_service = fields.Boolean()
    # Non-stored related field to allow portal user to
    # see the image of the product he has ordered
    product_image = fields.Binary(
        "Product Image", related="product_id.image_1024", store=False, related_sudo=True
    )
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
    channel_type = fields.Selection(
        [
            ("door", "Door"),
            ("mail", "Mail"),
            ("phone", "Phone"),
            ("call", "Call Center"),
            ("web", "Web"),
        ],
        string="Sales Channel",
    )
    price_unit = fields.Float(
        "Unit Price",
        digits=("Product Price"),
        compute="_compute_price_unit",
        store=True,
        readonly=False,
    )
    discount = fields.Float(string="Discount (%)", digits=("Discount"), default=0.0)
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
        string="Subtotal", readonly=True, store=True, compute="_compute_amount_service"
    )
    price_total = fields.Monetary(
        string="Total", readonly=True, store=True, compute="_compute_amount_service"
    )
    price_tax = fields.Float(
        string="Taxes Amount",
        readonly=True,
        store=True,
        compute="_compute_amount_service",
    )

    # Compute and Search methods
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

    @api.depends("reservation_id.checkin", "reservation_id.checkout", "product_id")
    def _compute_service_line_ids(self):
        for service in self:
            if service.product_id:
                day_qty = 1
                if service.reservation_id and service.product_id:
                    reservation = service.reservation_id
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
                            old_line = service._search_old_lines(idate)
                            if idate in [
                                line.date for line in service.service_line_ids
                            ]:
                                # REVIEW: If the date is already
                                # cached (otherwise double the date)
                                pass
                            elif not old_line:
                                lines.append(
                                    (
                                        0,
                                        False,
                                        {
                                            "date": idate,
                                            "day_qty": day_qty,
                                        },
                                    )
                                )
                            else:
                                lines.append((4, old_line.id))
                        move_day = 0
                        if consumed_on == "after":
                            move_day = 1
                        service.service_line_ids -= (
                            service.service_line_ids.filtered_domain(
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
                            )
                        )
                        _logger.info(service)
                        _logger.info(lines)
                        service.service_line_ids = lines
                    else:
                        # TODO: Review (business logic refact) no per_day logic service
                        if not service.service_line_ids:
                            service.service_line_ids = [
                                (
                                    0,
                                    False,
                                    {
                                        "date": fields.Date.today(),
                                        "day_qty": day_qty,
                                    },
                                )
                            ]
                else:
                    # TODO: Service without reservation(room) but with folio¿?
                    # example: tourist tour in group
                    if not service.service_line_ids:
                        service.service_line_ids = [
                            (
                                0,
                                False,
                                {
                                    "date": fields.Date.today(),
                                    "day_qty": day_qty,
                                },
                            )
                        ]
            else:
                service.service_line_ids = False

    def _search_old_lines(self, date):
        self.ensure_one()
        if isinstance(self._origin.id, int):
            old_line = self._origin.service_line_ids.filtered(lambda r: r.date == date)
            return old_line
        return False

    @api.depends("product_id")
    def _compute_tax_ids(self):
        for service in self:
            service.tax_ids = service.product_id.taxes_id.filtered(
                lambda r: not service.company_id or r.company_id == service.company_id
            )

    @api.depends("service_line_ids", "service_line_ids.day_qty")
    def _compute_product_qty(self):
        self.product_qty = 0
        _logger.info("B")
        for service in self.filtered("service_line_ids"):
            qty = sum(service.service_line_ids.mapped("day_qty"))
            service.product_qty = qty

    @api.depends("product_id", "service_line_ids", "reservation_id.pricelist_id")
    def _compute_price_unit(self):
        for service in self:
            folio = service.folio_id
            reservation = service.reservation_id
            origin = reservation if reservation else folio
            if origin:
                if service._recompute_price():
                    partner = origin.partner_id
                    pricelist = origin.pricelist_id
                    if reservation and service.is_board_service:
                        board_room_type = reservation.board_service_room_id
                        if board_room_type.price_type == "fixed":
                            service.price_unit = (
                                self.env["pms.board.service.room.type.line"]
                                .search(
                                    [
                                        (
                                            "pms_board_service_room_type_id",
                                            "=",
                                            board_room_type.id,
                                        ),
                                        ("product_id", "=", service.product_id.id),
                                    ]
                                )
                                .amount
                            )
                        else:
                            service.price_unit = (
                                reservation.price_total
                                * self.env["pms.board.service.room.type.line"]
                                .search(
                                    [
                                        (
                                            "pms_board_service_room_type_id",
                                            "=",
                                            board_room_type.id,
                                        ),
                                        ("product_id", "=", service.product_id.id),
                                    ]
                                )
                                .amount
                            ) / 100
                    else:
                        product = service.product_id.with_context(
                            lang=partner.lang,
                            partner=partner.id,
                            quantity=service.product_qty,
                            date=folio.date_order if folio else fields.Date.today(),
                            pricelist=pricelist.id,
                            uom=service.product_id.uom_id.id,
                            fiscal_position=False,
                        )
                        service.price_unit = self.env[
                            "account.tax"
                        ]._fix_tax_included_price_company(
                            service._get_display_price(product),
                            product.taxes_id,
                            service.tax_ids,
                            origin.company_id,
                        )
                else:
                    service.price_unit = service._origin.price_unit
            else:
                service.price_unit = 0

    def _recompute_price(self):
        # REVIEW: Conditional to avoid overriding already calculated prices,
        # I'm not sure it's the best way
        self.ensure_one()
        # folio/reservation origin service
        folio_origin = self._origin.folio_id
        reservation_origin = self._origin.reservation_id
        origin = reservation_origin if reservation_origin else folio_origin
        # folio/reservation new service
        folio_new = self.folio_id
        reservation_new = self.reservation_id
        new = reservation_new if reservation_new else folio_new
        price_fields = ["pricelist_id", "reservation_type"]
        if (
            any(origin[field] != new[field] for field in price_fields)
            or self._origin.price_unit == 0
        ):
            return True
        return False

    @api.depends("qty_invoiced", "product_qty", "folio_id.state")
    def _compute_get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order,
        the quantity to invoice is calculated from the ordered quantity.
        Otherwise, the quantity delivered is used.
        """
        for line in self:
            if line.folio_id.state not in ["draft"]:
                line.qty_to_invoice = line.product_qty - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    @api.depends("move_line_ids.move_id.state", "move_line_ids.quantity")
    def _compute_get_invoice_qty(self):
        """
        Compute the quantity invoiced. If case of a refund,
        the quantity invoiced is decreased. Note that this is the case only
        if the refund is generated from the Folio and that is intentional: if
        a refund made would automatically decrease the invoiced quantity,
        then there is a risk of reinvoicing it automatically, which may
        not be wanted at all. That's why the refund has to be
        created from the Folio
        """
        for line in self:
            qty_invoiced = 0.0
            for invoice_line in line.move_line_ids:
                if invoice_line.move_id.state != "cancel":
                    if invoice_line.move_id.type == "out_invoice":
                        qty_invoiced += invoice_line.uom_id._compute_quantity(
                            invoice_line.quantity, line.product_id.uom_id
                        )
                    elif invoice_line.move_id.type == "out_refund":
                        qty_invoiced -= invoice_line.uom_id._compute_quantity(
                            invoice_line.quantity, line.product_id.uom_id
                        )
            line.qty_invoiced = qty_invoiced

    @api.depends("product_qty", "qty_to_invoice", "qty_invoiced")
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a SO line. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done',
          we consider that there is nothing to invoice.
          This is also hte default value if the conditions of no other
          status is met.
        - to invoice: we refer to the quantity to invoice of the line.
          Refer to method `_compute_get_to_invoice_qty()` for more information on
          how this quantity is calculated.
        - upselling: this is possible only for a product invoiced on ordered
          quantities for which we delivered more than expected.
          The could arise if, for example, a project took more time than
          expected but we decided not to invoice the extra cost to the
          client. This occurs onyl in state 'sale', so that when a Folio
          is set to done, the upselling opportunity is removed from the list.
        - invoiced: the quantity invoiced is larger or equal to the
          quantity ordered.
        """
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        for line in self:
            state = line.folio_id.state or "draft"
            if state in ("draft"):
                line.invoice_status = "no"
            elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                line.invoice_status = "to invoice"
            elif (
                float_compare(
                    line.qty_invoiced, line.product_qty, precision_digits=precision
                )
                >= 0
            ):
                line.invoice_status = "invoiced"
            else:
                line.invoice_status = "no"

    @api.depends("product_qty", "discount", "price_unit", "tax_ids")
    def _compute_amount_service(self):
        for service in self:
            folio = service.folio_id
            reservation = service.reservation_id
            currency = folio.currency_id if folio else reservation.currency_id
            product = service.product_id
            price = service.price_unit * (1 - (service.discount or 0.0) * 0.01)
            taxes = service.tax_ids.compute_all(
                price, currency, service.product_qty, product=product
            )
            service.update(
                {
                    "price_tax": sum(
                        t.get("amount", 0.0) for t in taxes.get("taxes", [])
                    ),
                    "price_total": taxes["total_included"],
                    "price_subtotal": taxes["total_excluded"],
                }
            )

    # Action methods
    def open_service_ids(self):
        action = self.env.ref("pms.action_pms_services_form").read()[0]
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
        if origin.pricelist_id.discount_policy == "with_discount":
            return product.with_context(pricelist=origin.pricelist_id.id).price
        product_context = dict(
            self.env.context,
            partner_id=origin.partner_id.id,
            date=folio.date_order if folio else fields.Date.today(),
            uom=self.product_id.uom_id.id,
        )
        final_price, rule_id = origin.pricelist_id.with_context(
            product_context
        ).get_product_price_rule(
            self.product_id, self.product_qty or 1.0, origin.partner_id
        )
        base_price, currency_id = self.with_context(
            product_context
        )._get_real_price_currency(
            product,
            rule_id,
            self.product_qty,
            self.product_id.uom_id,
            origin.pricelist_id.id,
        )
        if currency_id != origin.pricelist_id.currency_id.id:
            base_price = (
                self.env["res.currency"]
                .browse(currency_id)
                .with_context(product_context)
                .compute(base_price, origin.pricelist_id.currency_id)
            )
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    # Businness Methods
    def _service_day_qty(self):
        self.ensure_one()
        qty = self.product_qty if len(self.service_line_ids) == 1 else 0
        if not self.reservation_id:
            return qty
        # TODO: Pass per_person to service line from product default_per_person
        if self.product_id.per_person:
            qty = self.reservation_id.adults
        return qty
