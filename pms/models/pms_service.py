# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from datetime import timedelta

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


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
            ("to invoice", "To Invoice"),
            ("no", "Nothing to Invoice"),
        ],
    )
    channel_type = fields.Selection(
        string="Sales Channel",
        help="sales channel through which the service was sold."
        "It can be 'door', 'mail', 'phone', 'call' or 'web'",
        selection=[
            ("door", "Door"),
            ("mail", "Mail"),
            ("phone", "Phone"),
            ("call", "Call Center"),
            ("web", "Web"),
        ],
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
        help="Total price without taxes",
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
        "reservation_id.checkin",
        "reservation_id.checkout",
        "product_id",
        "reservation_id.adults",
    )
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
        if origin.pricelist_id.discount_policy == "with_discount":
            return product.price
        final_price, rule_id = origin.pricelist_id.with_context(
            product._context
        ).get_product_price_rule(product, self.product_qty or 1.0, origin.partner_id)
        base_price, currency_id = self.with_context(
            product._context
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
                .with_context(product._context)
                .compute(base_price, origin.pricelist_id.currency_id)
            )
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        """Retrieve the price before applying the pricelist
        :param obj product: object of current product record
        :parem float qty: total quantity of product
        :param tuple price_and_rule: tuple(price, suitable_rule)
            coming from pricelist computation
        :param obj uom: unit of measure of current order line
        :param integer pricelist_id: pricelist id of sales order"""
        PricelistItem = self.env["product.pricelist.item"]
        field_name = "lst_price"
        currency_id = None
        product_currency = product.currency_id
        if rule_id:
            pricelist_item = PricelistItem.browse(rule_id)
            if pricelist_item.pricelist_id.discount_policy == "without_discount":
                while (
                    pricelist_item.base == "pricelist"
                    and pricelist_item.base_pricelist_id
                    and pricelist_item.base_pricelist_id.discount_policy
                    == "without_discount"
                ):
                    price, rule_id = pricelist_item.base_pricelist_id.with_context(
                        uom=uom.id
                    ).get_product_price_rule(product, qty, self.order_id.partner_id)
                    pricelist_item = PricelistItem.browse(rule_id)

            if pricelist_item.base == "standard_price":
                field_name = "standard_price"
                product_currency = product.cost_currency_id
            elif (
                pricelist_item.base == "pricelist" and pricelist_item.base_pricelist_id
            ):
                field_name = "price"
                product = product.with_context(
                    pricelist=pricelist_item.base_pricelist_id.id
                )
                product_currency = pricelist_item.base_pricelist_id.currency_id
            currency_id = pricelist_item.pricelist_id.currency_id

        if not currency_id:
            currency_id = product_currency
            cur_factor = 1.0
        else:
            if currency_id.id == product_currency.id:
                cur_factor = 1.0
            else:
                cur_factor = currency_id._get_conversion_rate(
                    product_currency,
                    currency_id,
                    self.company_id or self.env.company,
                    self.folio_id.date_order or fields.Date.today(),
                )

        product_uom = self.env.context.get("uom") or product.uom_id.id
        if uom and uom.id != product_uom:
            # the unit price is in a different uom
            uom_factor = uom._compute_price(1.0, product.uom_id)
        else:
            uom_factor = 1.0

        return product[field_name] * uom_factor * cur_factor, currency_id

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

    def _get_price_unit_line(self, date=False):
        self.ensure_one()
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
                property=self.reservation_id.pms_property_id.id,
            )
            if date:
                product_context["consumption_date"] = date
            if reservation and self.is_board_service:
                product_context["board_service"] = reservation.board_service_room_id.id
            product = self.product_id.with_context(product_context)
            return self.env["account.tax"]._fix_tax_included_price_company(
                self._get_display_price(product),
                product.taxes_id,
                self.tax_ids,
                origin.company_id,
            )
        else:
            return 0
