# Copyright 2020  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta
from math import ceil

import babel.dates
from dateutil import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import float_compare
from odoo.tools.misc import get_lang


class FolioSaleLine(models.Model):
    _name = "folio.sale.line"
    _description = "Folio Sale Line"
    _order = (
        "folio_id, sequence, reservation_order desc, service_order, name, date_order"
    )
    _check_company_auto = True

    folio_id = fields.Many2one(
        string="Folio Reference",
        help="Folio to which folio sale line belongs",
        required=True,
        index=True,
        copy=False,
        comodel_name="pms.folio",
        ondelete="cascade",
    )
    reservation_id = fields.Many2one(
        string="Reservation Reference",
        help="Reservation to which folio sale line belongs",
        index=True,
        copy=False,
        comodel_name="pms.reservation",
        ondelete="cascade",
    )
    service_id = fields.Many2one(
        string="Service Reference",
        help="Sevice included in folio sale line",
        index=True,
        copy=False,
        comodel_name="pms.service",
        ondelete="cascade",
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Property with access to the element;",
        readonly=True,
        store=True,
        comodel_name="pms.property",
        related="folio_id.pms_property_id",
        check_pms_properties=True,
    )
    is_board_service = fields.Boolean(
        string="Board Service",
        help="Indicates if the service included in "
        "folio sale line is part of a board service",
        store=True,
        related="service_id.is_board_service",
    )
    name = fields.Text(
        string="Description",
        help="Description of folio sale line",
        readonly=False,
        store=True,
        compute="_compute_name",
    )
    reservation_line_ids = fields.Many2many(
        string="Nights",
        help="Reservation lines associated with folio sale line,"
        " they corresponds with nights",
        comodel_name="pms.reservation.line",
    )
    service_line_ids = fields.Many2many(
        string="Service Lines",
        help="Subservices included in folio sale line service",
        comodel_name="pms.service.line",
    )
    sequence = fields.Integer(string="Sequence", help="", default=10)

    invoice_lines = fields.Many2many(
        string="Invoice Lines",
        copy=False,
        help="Folio sale line invoice lines",
        comodel_name="account.move.line",
        relation="folio_sale_line_invoice_rel",
        column1="sale_line_id",
        column2="invoice_line_id",
    )
    invoice_status = fields.Selection(
        string="Invoice Status",
        help="Invoice Status; it can be: upselling, invoiced, to invoice, no",
        readonly=True,
        store=True,
        selection=[
            ("upselling", "Upselling Opportunity"),
            ("invoiced", "Fully Invoiced"),
            ("to_invoice", "To Invoice"),
            ("no", "Nothing to Invoice"),
        ],
        compute="_compute_invoice_status",
    )
    price_unit = fields.Float(
        string="Unit Price",
        help="Unit Price of folio sale line",
        digits="Product Price",
    )

    price_subtotal = fields.Monetary(
        string="Subtotal",
        help="Subtotal price without taxes",
        readonly=True,
        store=True,
        compute="_compute_amount",
    )
    price_tax = fields.Float(
        string="Total Tax",
        help="Total of taxes in a reservation",
        readonly=True,
        store=True,
        compute="_compute_amount",
    )
    price_total = fields.Monetary(
        string="Total",
        help="Total price with taxes",
        readonly=True,
        store=True,
        compute="_compute_amount",
    )
    price_reduce = fields.Float(
        string="Price Reduce",
        help="Reduced price amount, that is, total price with discounts applied",
        readonly=True,
        store=True,
        digits="Product Price",
        compute="_compute_get_price_reduce",
    )
    tax_ids = fields.Many2many(
        string="Taxes",
        help="Taxes applied in the folio sale line",
        store=True,
        comodel_name="account.tax",
        compute="_compute_tax_ids",
        domain=["|", ("active", "=", False), ("active", "=", True)],
    )
    price_reduce_taxinc = fields.Monetary(
        string="Price Reduce Tax inc",
        help="Price with discounts applied and taxes included",
        readonly=True,
        store=True,
        compute="_compute_get_price_reduce_tax",
    )
    price_reduce_taxexcl = fields.Monetary(
        string="Price Reduce Tax excl",
        help="Price with discounts applied without taxes",
        readonly=True,
        store=True,
        compute="_compute_get_price_reduce_notax",
    )

    discount = fields.Float(
        string="Discount (%)",
        help="Discount of total price in folio sale line",
        readonly=False,
        store=True,
        digits="Discount",
        compute="_compute_discount",
    )

    product_id = fields.Many2one(
        string="Product",
        help="Product associated with folio sale line, "
        "can be product associated with service "
        "or product associated with"
        "reservation's room type, in other case it's false",
        store=True,
        comodel_name="product.product",
        domain="[('sale_ok', '=', True),\
            ('is_pms_available', '=', True),\
            '|', ('company_id', '=', False), \
            ('company_id', '=', company_id)]",
        ondelete="restrict",
        compute="_compute_product_id",
        check_company=True,
        change_default=True,
    )
    product_uom_qty = fields.Float(
        string="Quantity",
        help="",
        readonly=False,
        store=True,
        digits="Product Unit of Measure",
        compute="_compute_product_uom_qty",
    )
    product_uom = fields.Many2one(
        string="Unit of Measure",
        help="",
        comodel_name="uom.uom",
        domain="[('category_id', '=', product_uom_category_id)]",
    )
    product_uom_category_id = fields.Many2one(
        string="Unit of Measure Category",
        help="",
        readonly=True,
        related="product_id.uom_id.category_id",
    )
    product_uom_readonly = fields.Boolean(
        string="", help="", compute="_compute_product_uom_readonly"
    )

    product_custom_attribute_value_ids = fields.One2many(
        string="Custom Values",
        copy=True,
        comodel_name="product.attribute.custom.value",
        inverse_name="sale_order_line_id",
    )

    qty_to_invoice = fields.Float(
        string="To Invoice Quantity",
        help="The quantity to invoice. If the invoice policy is order, "
        "the quantity to invoice is calculated from the ordered quantity. "
        "Otherwise, the quantity delivered is used.",
        readonly=True,
        store=True,
        digits="Product Unit of Measure",
        compute="_compute_get_to_invoice_qty",
    )
    qty_invoiced = fields.Float(
        string="Invoiced Quantity",
        help="It is the amount invoiced when an invoice is issued",
        readonly=True,
        store=True,
        digits="Product Unit of Measure",
        compute="_compute_get_invoice_qty",
        compute_sudo=True,
    )

    untaxed_amount_invoiced = fields.Monetary(
        string="Untaxed Invoiced Amount",
        help="The amount to invoice without taxes in the line of folio",
        store=True,
        compute="_compute_untaxed_amount_invoiced",
        compute_sudo=True,
    )
    untaxed_amount_to_invoice = fields.Monetary(
        string="Untaxed Amount To Invoice",
        help="The invoiced amount without taxes in the line of the folio",
        store=True,
        compute="_compute_untaxed_amount_to_invoice",
        compute_sudo=True,
    )

    currency_id = fields.Many2one(
        string="Currency",
        help="The currency for the folio",
        readonly=True,
        store=True,
        depends=["folio_id.currency_id"],
        related="folio_id.currency_id",
    )
    company_id = fields.Many2one(
        string="Company",
        help="The company in the folio sale line",
        readonly=True,
        store=True,
        index=True,
        related="folio_id.company_id",
    )
    origin_agency_id = fields.Many2one(
        string="Origin Agency",
        help="The agency where the folio sale line originates",
        comodel_name="res.partner",
        domain="[('is_agency', '=', True)]",
        compute="_compute_origin_agency_id",
        store=True,
        readonly=False,
    )
    analytic_tag_ids = fields.Many2many(
        string="Analytic Tags",
        comodel_name="account.analytic.tag",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    analytic_line_ids = fields.One2many(
        string="Analytic lines",
        comodel_name="account.analytic.line",
        inverse_name="so_line",
    )
    is_downpayment = fields.Boolean(
        string="Is a down payment",
        help="Down payments are made when creating invoices from a folio."
        " They are not copied when duplicating a folio.",
    )

    state = fields.Selection(
        string="Folio Status",
        help="The status of the folio related with folio sale line",
        readonly=True,
        copy=False,
        store=True,
        related="folio_id.state",
    )

    display_type = fields.Selection(
        string="Display Type",
        help="Technical field for UX purpose.",
        selection=[("line_section", "Section"), ("line_note", "Note")],
        default=False,
    )

    service_order = fields.Integer(
        string="Service Id",
        help="Field to order by service id",
        readonly=True,
        store=True,
        compute="_compute_service_order",
    )

    reservation_order = fields.Integer(
        string="Reservation Id",
        help="Field to order by reservation id",
        readonly=True,
        store=True,
        compute="_compute_reservation_order",
    )

    date_order = fields.Date(
        string="Date",
        help="Field to order by service",
        readonly=True,
        store=True,
        compute="_compute_date_order",
    )
    default_invoice_to = fields.Many2one(
        string="Invoice to",
        help="""Indicates the contact to which this line will be
        billed by default, if it is not established,
        a guest or the generic contact will be used instead""",
        comodel_name="res.partner",
        ondelete="restrict",
    )
    autoinvoice_date = fields.Date(
        string="Autoinvoice Date",
        compute="_compute_autoinvoice_date",
        store=True,
    )

    @api.depends(
        "folio_id.agency_id",
        "reservation_line_ids",
        "service_line_ids",
    )
    def _compute_origin_agency_id(self):
        """
        Set the origin agency if the origin lines channel
        match with the agency's channel
        """
        for rec in self:
            # TODO: ServiceLines agency
            if rec.folio_id.agency_id and list(
                set(rec.reservation_line_ids.mapped("sale_channel_id.id"))
            ) == rec.folio_id.agency_id.mapped("sale_channel_id.id"):
                rec.origin_agency_id = rec.folio_id.agency_id
            else:
                rec.origin_agency_id = False

    @api.depends("qty_to_invoice")
    def _compute_service_order(self):
        for record in self:
            record.service_order = (
                record.service_id
                if record.service_id
                else -1
                if record.display_type
                else 0
            )

    @api.depends("service_order")
    def _compute_date_order(self):
        for record in self:
            if record.display_type:
                record.date_order = 0
            elif record.reservation_id and not record.service_id:
                record.date_order = (
                    min(record.reservation_line_ids.mapped("date"))
                    if record.reservation_line_ids
                    else 0
                )
            elif record.reservation_id and record.service_id:
                record.date_order = (
                    min(record.service_line_ids.mapped("date"))
                    if record.service_line_ids
                    else 0
                )
            else:
                record.date_order = 0

    @api.depends(
        "default_invoice_to",
        "invoice_status",
        "folio_id.last_checkout",
        "reservation_id.checkout",
        "service_id.reservation_id.checkout",
    )
    def _compute_autoinvoice_date(self):
        self.autoinvoice_date = False
        for record in self.filtered(lambda r: r.invoice_status == "to_invoice"):
            record.autoinvoice_date = record._get_to_invoice_date()

    def _get_to_invoice_date(self):
        self.ensure_one()
        partner = self.default_invoice_to
        if self.reservation_id:
            last_checkout = self.reservation_id.checkout
        elif self.service_id and self.service_id.reservation_id:
            last_checkout = self.service_id.reservation_id.checkout
        else:
            last_checkout = self.folio_id.last_checkout
        invoicing_policy = (
            self.pms_property_id.default_invoicing_policy
            if not partner or partner.invoicing_policy == "property"
            else partner.invoicing_policy
        )
        if invoicing_policy == "manual":
            return False
        if invoicing_policy == "checkout":
            margin_days = (
                self.pms_property_id.margin_days_autoinvoice
                if not partner or partner.invoicing_policy == "property"
                else partner.margin_days_autoinvoice
            )
            return last_checkout + timedelta(days=margin_days)
        if invoicing_policy == "month_day":
            month_day = (
                self.pms_property_id.invoicing_month_day
                if not partner or partner.invoicing_policy == "property"
                else partner.invoicing_month_day
            )
            if last_checkout.day <= month_day:
                self.autoinvoice_date = last_checkout.replace(day=month_day)
            else:
                self.autoinvoice_date = (
                    last_checkout + relativedelta.relativedelta(months=1)
                ).replace(day=month_day)

    @api.depends("date_order")
    def _compute_reservation_order(self):
        for record in self:
            record.reservation_order = (
                record.reservation_id if record.reservation_id else 0
            )

    @api.depends("reservation_line_ids", "service_line_ids", "service_line_ids.day_qty")
    def _compute_product_uom_qty(self):
        for line in self:
            if line.reservation_line_ids:
                line.product_uom_qty = len(line.reservation_line_ids)
            elif line.service_line_ids:
                line.product_uom_qty = sum(line.service_line_ids.mapped("day_qty"))
            elif not line.product_uom_qty:
                line.product_uom_qty = False

    @api.depends("state")
    def _compute_product_uom_readonly(self):
        for line in self:
            line.product_uom_readonly = line.state in ["sale", "done", "cancel"]

    @api.depends(
        "invoice_lines",
        "invoice_lines.price_total",
        "invoice_lines.move_id.state",
        "invoice_lines.move_id.move_type",
    )
    def _compute_untaxed_amount_invoiced(self):
        """Compute the untaxed amount already invoiced from
        the sale order line, taking the refund attached
        the so line into account. This amount is computed as
            SUM(inv_line.price_subtotal) - SUM(ref_line.price_subtotal)
        where
            `inv_line` is a customer invoice line linked to the SO line
            `ref_line` is a customer credit note (refund) line linked to the SO line
        """
        for line in self:
            amount_invoiced = 0.0
            for invoice_line in line.invoice_lines:
                if invoice_line.move_id.state == "posted":
                    invoice_date = (
                        invoice_line.move_id.invoice_date or fields.Date.today()
                    )
                    if invoice_line.move_id.move_type in ["out_invoice", "out_receipt"]:
                        amount_invoiced += invoice_line.currency_id._convert(
                            invoice_line.price_subtotal,
                            line.currency_id,
                            line.company_id,
                            invoice_date,
                        )
                    elif invoice_line.move_id.move_type == "out_refund":
                        amount_invoiced -= invoice_line.currency_id._convert(
                            invoice_line.price_subtotal,
                            line.currency_id,
                            line.company_id,
                            invoice_date,
                        )
            line.untaxed_amount_invoiced = amount_invoiced

    @api.depends(
        "state",
        "price_reduce",
        "product_id",
        "untaxed_amount_invoiced",
        "product_uom_qty",
    )
    def _compute_untaxed_amount_to_invoice(self):
        """Total of remaining amount to invoice on the sale order line (taxes excl.) as
            total_sol - amount already invoiced
        where Total_sol depends on the invoice policy of the product.

        Note: Draft invoice are ignored on purpose, the 'to invoice' amount should
        come only from the SO lines.
        """
        for line in self:
            amount_to_invoice = 0.0
            if line.state != "draft":
                # Note: do not use price_subtotal field as it returns
                # zero when the ordered quantity is zero.
                # It causes problem for expense line (e.i.: ordered qty = 0,
                # deli qty = 4, price_unit = 20 ; subtotal is zero),
                # but when you can invoice the line,
                # you see an amount and not zero.
                # Since we compute untaxed amount, we can use directly the price
                # reduce (to include discount) without using `compute_all()`
                # method on taxes.
                price_subtotal = 0.0
                price_subtotal = line.price_reduce * line.product_uom_qty
                if len(line.tax_ids.filtered(lambda tax: tax.price_include)) > 0:
                    # As included taxes are not excluded from the computed subtotal,
                    # `compute_all()` method has to be called to retrieve
                    # the subtotal without them.
                    # `price_reduce_taxexcl` cannot be used as it is computed from
                    # `price_subtotal` field. (see upper Note)
                    price_subtotal = line.tax_ids.compute_all(
                        price_subtotal,
                        currency=line.folio_id.currency_id,
                        quantity=line.product_uom_qty,
                        product=line.product_id,
                        partner=line.folio_id.partner_id,
                    )["total_excluded"]

                if any(
                    line.invoice_lines.mapped(lambda l: l.discount != line.discount)
                ):
                    # In case of re-invoicing with different
                    # discount we try to calculate manually the
                    # remaining amount to invoice
                    amount = 0
                    for inv_line in line.invoice_lines:
                        if (
                            len(
                                inv_line.tax_ids.filtered(lambda tax: tax.price_include)
                            )
                            > 0
                        ):
                            amount += inv_line.tax_ids.compute_all(
                                inv_line.currency_id._convert(
                                    inv_line.price_unit,
                                    line.currency_id,
                                    line.company_id,
                                    inv_line.date or fields.Date.today(),
                                    round=False,
                                )
                                * inv_line.quantity
                            )["total_excluded"]
                        else:
                            amount += (
                                inv_line.currency_id._convert(
                                    inv_line.price_unit,
                                    line.currency_id,
                                    line.company_id,
                                    inv_line.date or fields.Date.today(),
                                    round=False,
                                )
                                * inv_line.quantity
                            )

                    amount_to_invoice = max(price_subtotal - amount, 0)
                else:
                    amount_to_invoice = price_subtotal - line.untaxed_amount_invoiced

            line.untaxed_amount_to_invoice = amount_to_invoice

    @api.depends("state", "product_uom_qty", "qty_to_invoice", "qty_invoiced")
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a SO line:
        Its if compute based on reservations/services associated status
        """
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        for line in self:
            if line.state == "draft" or line.price_total == 0.0:
                line.invoice_status = "no"
            # REVIEW: if qty_to_invoice < 0 (invoice qty > sale qty),
            # why status to_invoice?? this behavior is copied from sale order
            # https://github.com/OCA/OCB/blob/14.0/addons/sale/models/sale.py#L1160
            elif line.qty_to_invoice > 0:
                line.invoice_status = "to_invoice"
            elif (
                float_compare(
                    line.qty_invoiced,
                    line.product_uom_qty,
                    precision_digits=precision,
                )
                >= 0
            ):
                line.invoice_status = "invoiced"
            else:
                line.invoice_status = "no"

    @api.depends("reservation_line_ids", "service_line_ids", "service_id")
    def _compute_name(self):
        for record in self:
            record.name = self.generate_folio_sale_name(
                record.reservation_id,
                record.product_id,
                record.service_id,
                record.reservation_line_ids,
                record.service_line_ids,
            )

    @api.depends("product_uom_qty", "discount", "price_unit", "tax_ids")
    def _compute_amount(self):
        """
        Compute the amounts of the Sale line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_ids.compute_all(
                price,
                line.folio_id.currency_id,
                line.product_uom_qty,
                product=line.product_id,
            )
            line.update(
                {
                    "price_tax": sum(
                        t.get("amount", 0.0) for t in taxes.get("taxes", [])
                    ),
                    "price_total": taxes["total_included"],
                    "price_subtotal": taxes["total_excluded"],
                }
            )
            if self.env.context.get(
                "import_file", False
            ) and not self.env.user.user_has_groups("account.group_account_manager"):
                line.tax_ids.invalidate_cache(
                    ["invoice_repartition_line_ids"], [line.tax_ids.id]
                )

    @api.depends("reservation_id.tax_ids", "service_id.tax_ids")
    def _compute_tax_ids(self):
        for record in self:
            if not record.display_type:
                record.tax_ids = (
                    record.service_id.tax_ids
                    if record.service_id
                    else record.reservation_id.tax_ids
                )
            else:
                record.tax_ids = False

    @api.depends(
        "service_id",
        "service_id.service_line_ids",
        "service_id.service_line_ids.discount",
    )
    def _compute_discount(self):
        """
        Only in services without room we compute discount,
        and this services only have one service line
        """
        for record in self:
            if record.service_id and not record.service_id.reservation_id:
                record.discount = record.service_id.service_line_ids.mapped("discount")[
                    0
                ]
            elif not record.discount:
                record.discount = 0

    @api.depends("reservation_id.room_type_id", "service_id.product_id")
    def _compute_product_id(self):
        for record in self.filtered("display_type"):
            if record.reservation_id and not record.service_id:
                record.product_id = record.reservation_id.room_type_id.product_id
            elif record.service_id:
                record.product_id = record.service_id.product_id
            else:
                record.product_id = False

    # @api.depends('product_id', 'folio_id.state', 'qty_invoiced', 'qty_delivered')
    # def _compute_product_updatable(self):
    #     for line in self:
    #         if line.state in ['done', 'cancel'] or (
    #                 line.state == 'sale' and (
    #                     line.qty_invoiced > 0 or line.qty_delivered > 0)):
    #             line.product_updatable = False
    #         else:
    #             line.product_updatable = True

    # no trigger product_id.invoice_policy to avoid retroactively changing SO
    @api.depends("qty_invoiced", "product_uom_qty", "folio_id.state")
    def _compute_get_to_invoice_qty(self):
        """
        Compute the quantity to invoice.
        If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity.
        Otherwise, the quantity delivered is used.
        """
        for line in self:
            if line.folio_id.state not in ["draft"]:
                line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    @api.depends(
        "invoice_lines.move_id.state",
        "invoice_lines.quantity",
        "untaxed_amount_to_invoice",
    )
    def _compute_get_invoice_qty(self):
        """
        Compute the quantity invoiced. If case of a refund,
        the quantity invoiced is decreased. Note
        that this is the case only if the refund is
        generated from the Folio and that is intentional: if
        a refund made would automatically decrease the invoiced quantity,
        then there is a risk of reinvoicing
        it automatically, which may not be wanted at all.
        That's why the refund has to be created from the Folio
        """
        for line in self:
            qty_invoiced = 0.0
            for invoice_line in line.invoice_lines:
                if invoice_line.move_id.state != "cancel":
                    if invoice_line.move_id.move_type in ["out_invoice", "out_receipt"]:
                        qty_invoiced += invoice_line.product_uom_id._compute_quantity(
                            invoice_line.quantity, line.product_uom
                        )
                    elif invoice_line.move_id.move_type == "out_refund":
                        if (
                            not line.is_downpayment
                            or line.untaxed_amount_to_invoice == 0
                        ):
                            qty_invoiced -= (
                                invoice_line.product_uom_id._compute_quantity(
                                    invoice_line.quantity, line.product_uom
                                )
                            )
            line.qty_invoiced = qty_invoiced

    @api.depends("price_unit", "discount")
    def _compute_get_price_reduce(self):
        for line in self:
            line.price_reduce = line.price_unit * (1.0 - line.discount / 100.0)

    @api.depends("price_total", "product_uom_qty")
    def _compute_get_price_reduce_tax(self):
        for line in self:
            line.price_reduce_taxinc = (
                line.price_total / line.product_uom_qty if line.product_uom_qty else 0.0
            )

    @api.depends("price_subtotal", "product_uom_qty")
    def _compute_get_price_reduce_notax(self):
        for line in self:
            line.price_reduce_taxexcl = (
                line.price_subtotal / line.product_uom_qty
                if line.product_uom_qty
                else 0.0
            )

    # @api.model
    # def _prepare_add_missing_fields(self, values):
    #     """ Deduce missing required fields from the onchange """
    #     res = {}
    #     onchange_fields = ['name', 'price_unit', 'product_uom', 'tax_ids']
    #     if values.get('folio_id') and values.get('product_id') and any(
    #             f not in values for f in onchange_fields
    #             ):
    #         line = self.new(values)
    #         line.product_id_change()
    #         for field in onchange_fields:
    #             if field not in values:
    #                 res[field] = line._fields[field].convert_to_write(
    #                     line[field], line
    #                     )
    #     return res

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for values in vals_list:
    #         if values.get('display_type', self.default_get(
    #                 ['display_type'])['display_type']
    #                 ):
    #             values.update(product_id=False, price_unit=0,
    #                 product_uom_qty=0, product_uom=False,
    #                 customer_lead=0)

    #         values.update(self._prepare_add_missing_fields(values))

    #     lines = super().create(vals_list)
    #     for line in lines:
    #         if line.product_id and line.folio_id.state == 'sale':
    #             msg = _("Extra line with %s ") % (line.product_id.display_name,)
    #             line.folio_id.message_post(body=msg)
    #             # create an analytic account if at least an expense product
    #             if line.product_id.expense_policy not in [False, 'no'] and \
    #                     not line.folio_id.analytic_account_id:
    #                 line.folio_id._create_analytic_account()
    #     return lines

    # _sql_constraints = [
    #     ('accountable_required_fields',
    #         "CHECK(display_type IS NOT NULL OR \
    #             (product_id IS NOT NULL AND product_uom IS NOT NULL))",
    #         "Missing required fields on accountable sale order line."),
    #     ('non_accountable_null_fields',
    #         "CHECK(display_type IS NULL OR (product_id IS NULL AND \
    #             price_unit = 0 AND product_uom_qty = 0 AND \
    #                 product_uom IS NULL AND customer_lead = 0))",
    #         "Forbidden values on non-accountable sale order line"),
    # ]
    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        if operator in ("ilike", "like", "=", "=like", "=ilike"):
            args = expression.AND(
                [
                    args or [],
                    ["|", ("folio_id.name", operator, name), ("name", operator, name)],
                ]
            )
        return super(FolioSaleLine, self)._name_search(
            name, args=args, operator=operator, limit=limit, name_get_uid=name_get_uid
        )

    def name_get(self):
        result = []
        for so_line in self.sudo():
            name = "{} - {}".format(
                so_line.folio_id.name,
                so_line.name and so_line.name.split("\n")[0] or so_line.product_id.name,
            )
            result.append((so_line.id, name))
        return result

    @api.model
    def generate_folio_sale_name(
        self,
        reservation_id,
        product_id,
        service_id,
        reservation_line_ids,
        service_line_ids,
        qty=False,
    ):
        if reservation_line_ids:
            month = False
            name = False
            lines = reservation_line_ids.sorted(key="date")
            for index, date in enumerate(lines.mapped("date")):
                if qty and index > (qty - 1):
                    break
                if date.month != month:
                    name = name + "\n" if name else ""
                    name += (
                        babel.dates.format_date(
                            date=date, format="MMMM y", locale=get_lang(self.env).code
                        )
                        + ": "
                    )
                    name += date.strftime("%d")
                    month = date.month
                else:
                    name += ", " + date.strftime("%d")

            return "{} ({}).".format(product_id.name, name)
        elif service_line_ids:
            month = False
            name = False
            lines = service_line_ids.filtered(
                lambda x: x.service_id == service_id
            ).sorted(key="date")

            for index, date in enumerate(lines.mapped("date")):
                if qty and index > (ceil(qty / reservation_id.adults) - 1):
                    break
                if date.month != month:
                    name = name + "\n" if name else ""
                    name += (
                        babel.dates.format_date(
                            date=date, format="MMMM y", locale=get_lang(self.env).code
                        )
                        + ": "
                    )
                    name += date.strftime("%d")
                    month = date.month
                else:
                    name += ", " + date.strftime("%d")
            return "{} ({}).".format(service_id.name, name)
        else:
            return service_id.name

    def _get_invoice_line_sequence(self, new=0, old=0):
        """
        Method intended to be overridden in third-party
        module if we want to prevent the resequencing of invoice lines.

        :param int new:   the new line sequence
        :param int old:   the old line sequence

        :return:          the sequence of the SO line, by default the new one.
        """
        return new or old

    def _update_line_quantity(self, values):
        folios = self.mapped("folio_id")
        for order in folios:
            order_lines = self.filtered(lambda x: x.folio_id == order)
            msg = "<b>" + _("The ordered quantity has been updated.") + "</b><ul>"
            for line in order_lines:
                msg += "<li> %s: <br/>" % line.product_id.display_name
                msg += (
                    _(
                        "Ordered Quantity: %(old_qty)s -> %(new_qty)s",
                        old_qty=line.product_uom_qty,
                        new_qty=values["product_uom_qty"],
                    )
                    + "<br/>"
                )
                # if line.product_id.type in ('consu', 'product'):
                #     msg += _("Delivered Quantity: %s", line.qty_delivered) + "<br/>"
                msg += _("Invoiced Quantity: %s", line.qty_invoiced) + "<br/>"
            msg += "</ul>"
            order.message_post(body=msg)

    def write(self, values):
        # Prevent writing on a locked Folio or folio sale lines invoiced.
        protected_fields = self._get_protected_fields()
        protected_fields_modified_list = list(
            set(protected_fields) & set(values.keys())
        )
        fields_modified = self.env["ir.model.fields"].search(
            [("name", "in", protected_fields_modified_list), ("model", "=", self._name)]
        )
        if fields_modified:
            if self.filtered(
                lambda l: any(
                    values.get(field.name) != getattr(l, field.name)
                    for field in fields_modified
                )
            ) and (
                "done" in self.mapped("folio_id.state")
                or self.invoice_lines.filtered(
                    lambda l: l.move_id.state == "posted"
                    and l.move_id.move_type == "out_invoice"
                    and l.move_id.payment_state != "reversed"
                )
            ):
                raise UserError(
                    _(
                        """It is forbidden to modify the following fields
                        in a locked folio (fields already invoiced):\n%s"""
                    )
                    % "\n".join(fields_modified.mapped("field_description"))
                )
            if "draft" in self.mapped("invoice_lines.move_id.state"):
                if "product_uom_qty" in values:
                    for line in self:
                        if line.qty_invoiced > values["product_uom_qty"]:
                            raise UserError(
                                _(
                                    "This quantity was already invoiced."
                                    " You must reduce the invoiced quantity first."
                                )
                            )
                for line in self.filtered(lambda l: not l.display_type):
                    if "product_uom_qty" in values:
                        line._update_line_quantity(values)
                    mapped_fields = self._get_mapped_move_line_fields()
                    move_line_vals = [
                        (
                            1,
                            line.invoice_lines[0].id,
                            {
                                mapped_fields[field]: values[field]
                                for field in fields_modified.mapped("name")
                            },
                        )
                    ]
                    line[0].invoice_lines.move_id.write(
                        {"invoice_line_ids": move_line_vals}
                    )

        result = super(FolioSaleLine, self).write(values)
        return result

    def _prepare_invoice_line(self, qty=False, **optional_values):
        """
        Prepare the dict of values to create the new invoice line for a folio sale line.

        :param qty: float quantity to invoice
        :param optional_values: any parameter that
            should be added to the returned invoice line
        """
        self.ensure_one()
        if self.is_downpayment:
            downpayment_invoice = self.folio_id.move_ids.filtered(
                lambda x: x.payment_state != "reversed"
                and x.line_ids.filtered(lambda l: l.folio_line_ids == self)
            )
            name = self.name + " (" + downpayment_invoice.name + ")"
        else:
            name = self.name
        res = {
            "display_type": self.display_type,
            "sequence": self.sequence,
            "name": name,
            "product_id": self.product_id.id,
            "product_uom_id": self.product_uom.id,
            "quantity": qty if qty else self.qty_to_invoice,
            "discount": self.discount,
            "price_unit": self.price_unit,
            "tax_ids": [(6, 0, self.tax_ids.ids)],
            "analytic_account_id": self.folio_id.analytic_account_id.id,
            "analytic_tag_ids": [(6, 0, self.analytic_tag_ids.ids)],
            "folio_line_ids": [(6, 0, [self.id])],
            "name_changed_by_user": False,
        }
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res["account_id"] = False
        return res

    def _check_line_unlink(self):
        """
        Check wether a line can be deleted or not.

        Lines cannot be deleted if the folio is confirmed; downpayment
        lines who have not yet been invoiced bypass that exception.
        :rtype: recordset folio.sale.line
        :returns: set of lines that cannot be deleted
        """
        return self.filtered(
            lambda line: line.state not in ("draft")
            and (line.invoice_lines or not line.is_downpayment)
        )

    # def unlink(self):
    #     if self._check_line_unlink():
    #         raise UserError(
    #             _("""You can not remove an sale line once the sales
    #               folio is confirmed.\n
    #               You should rather set the quantity to 0.""")
    #         )
    #     return super(FolioSaleLine, self).unlink()

    def _get_real_price_currency(self, product, rule_id, qty, uom, pricelist_id):
        """Retrieve the price before applying the pricelist
        :param obj product: object of current product record
        :parem float qty: total quentity of product
        :param tuple price_and_rule: tuple(price, suitable_rule)
            coming from pricelist computation
        :param obj uom: unit of measure of current folio line
        :param integer pricelist_id: pricelist id of folio"""
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
                    ).get_product_price_rule(product, qty, self.folio_id.partner_id)
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

    def _get_protected_fields(self):
        return [
            "product_id",
            "price_unit",
            "product_uom",
            "tax_ids",
            "analytic_tag_ids",
            "discount",
        ]

    def _get_mapped_move_line_fields(self):
        return {
            "product_id": "product_id",
            "price_unit": "price_unit",
            "product_uom": "product_uom_id",
            "tax_ids": "tax_ids",
            "analytic_tag_ids": "analytic_tag_ids",
            "discount": "discount",
        }
