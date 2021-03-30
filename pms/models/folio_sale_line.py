# Copyright 2020  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.osv import expression
from odoo.tools import float_compare, float_is_zero


class FolioSaleLine(models.Model):
    _name = "folio.sale.line"
    _description = "Folio Sale Line"
    _order = "folio_id, sequence, id"
    _check_company_auto = True

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
            if line.state == "draft":
                line.invoice_status = "no"
            # REVIEW: if qty_to_invoice < 0 (invoice qty > sale qty),
            # why status to_invoice?? this behavior is copied from sale order
            # https://github.com/OCA/OCB/blob/14.0/addons/sale/models/sale.py#L1160
            elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                line.invoice_status = "to invoice"
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

    @api.depends("reservation_line_ids", "service_id")
    def _compute_name(self):
        for record in self:
            if not record.name_updated:
                record.name = record._get_compute_name()

    @api.depends("name")
    def _compute_name_updated(self):
        self.name_updated = False
        for record in self.filtered("name"):
            if record.name != record._get_compute_name():
                record.name_updated = True

    def _get_compute_name(self):
        self.ensure_one()
        if self.reservation_line_ids:
            month = False
            name = False
            lines = self.reservation_line_ids.sorted("date")
            for date in lines.mapped("date"):
                if date.month != month:
                    name = name + "\n" if name else ""
                    name += date.strftime("%B-%Y") + ": "
                    name += date.strftime("%d")
                    month = date.month
                else:
                    name += ", " + date.strftime("%d")
            return name
        elif self.service_id:
            return self.service_id.name
        else:
            return False

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
            record.tax_ids = (
                record.service_id.tax_ids
                if record.service_id
                else record.reservation_id.tax_ids
            )

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
        for record in self:
            if record.reservation_id:
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
                    if invoice_line.move_id.move_type == "out_invoice":
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

    # def write(self, values):
    #     if 'display_type' in values and self.filtered(
    #           lambda line: line.display_type != values.get('display_type')):
    #         raise UserError(_("You cannot change the type of a sale order line.\
    #           Instead you should delete the current line and create \
    #           a new line of the proper type."))

    #     if 'product_uom_qty' in values:
    #         precision = self.env['decimal.precision'].precision_get(
    #           'Product Unit of Measure'
    #         )
    #         self.filtered(
    #             lambda r: r.state == 'sale' and \
    #                 float_compare(
    #                     r.product_uom_qty,
    #                     values['product_uom_qty'],
    #                     precision_digits=precision) != 0)._update_line_quantity(
    #                         values
    #                         )

    #     # Prevent writing on a locked SO.
    #     protected_fields = self._get_protected_fields()
    #     if 'done' in self.mapped('folio_id.state') and any(
    #             f in values.keys() for f in protected_fields
    #             ):
    #         protected_fields_modified = list(set(protected_fields) & set(
    #             values.keys()
    #             ))
    #         fields = self.env['ir.model.fields'].search([
    #             ('name', 'in', protected_fields_modified),
    #             ('model', '=', self._name)
    #         ])
    #         raise UserError(
    #             _('It is forbidden to modify the following \
    #              fields in a locked order:\n%s')
    #             % '\n'.join(fields.mapped('field_description'))
    #         )

    #     result = super(SaleOrderLine, self).write(values)
    #     return result

    folio_id = fields.Many2one(
        "pms.folio",
        string="Folio Reference",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
    )
    reservation_id = fields.Many2one(
        "pms.reservation",
        string="Reservation Reference",
        ondelete="cascade",
        index=True,
        copy=False,
    )
    service_id = fields.Many2one(
        "pms.service",
        string="Service Reference",
        ondelete="cascade",
        index=True,
        copy=False,
    )
    is_board_service = fields.Boolean(
        string="Board Service",
        related="service_id.is_board_service",
        store=True,
    )

    name = fields.Text(
        string="Description", compute="_compute_name", store=True, readonly=False
    )
    name_updated = fields.Boolean(compute="_compute_name_updated", store=True)
    reservation_line_ids = fields.Many2many(
        "pms.reservation.line",
        string="Nights",
    )
    service_line_ids = fields.Many2many(
        "pms.service.line",
        string="Service Lines",
    )
    sequence = fields.Integer(string="Sequence", default=10)

    invoice_lines = fields.Many2many(
        "account.move.line",
        "folio_sale_line_invoice_rel",
        "sale_line_id",
        "invoice_line_id",
        string="Invoice Lines",
        copy=False,
    )
    invoice_status = fields.Selection(
        [
            ("upselling", "Upselling Opportunity"),
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
    price_unit = fields.Float(
        "Unit Price",
        digits="Product Price",
    )

    price_subtotal = fields.Monetary(
        compute="_compute_amount", string="Subtotal", readonly=True, store=True
    )
    price_tax = fields.Float(
        compute="_compute_amount", string="Total Tax", readonly=True, store=True
    )
    price_total = fields.Monetary(
        compute="_compute_amount", string="Total", readonly=True, store=True
    )
    price_reduce = fields.Float(
        compute="_compute_get_price_reduce",
        string="Price Reduce",
        digits="Product Price",
        readonly=True,
        store=True,
    )
    tax_ids = fields.Many2many(
        "account.tax",
        compute="_compute_tax_ids",
        store=True,
        string="Taxes",
        domain=["|", ("active", "=", False), ("active", "=", True)],
    )
    price_reduce_taxinc = fields.Monetary(
        compute="_compute_get_price_reduce_tax",
        string="Price Reduce Tax inc",
        readonly=True,
        store=True,
    )
    price_reduce_taxexcl = fields.Monetary(
        compute="_compute_get_price_reduce_notax",
        string="Price Reduce Tax excl",
        readonly=True,
        store=True,
    )

    discount = fields.Float(
        string="Discount (%)",
        digits="Discount",
        compute="_compute_discount",
        readonly=False,
        store=True,
    )

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        domain="[('sale_ok', '=', True),\
            '|', ('company_id', '=', False), \
            ('company_id', '=', company_id)]",
        change_default=True,
        ondelete="restrict",
        check_company=True,
        compute="_compute_product_id",
        store=True,
    )
    # product_updatable = fields.Boolean(
    #   compute='_compute_product_updatable',
    #   string='Can Edit Product',
    #   readonly=True,
    #   default=True)
    product_uom_qty = fields.Float(
        string="Quantity",
        digits="Product Unit of Measure",
        compute="_compute_product_uom_qty",
        store=True,
        readonly=False,
    )
    product_uom = fields.Many2one(
        "uom.uom",
        string="Unit of Measure",
        domain="[('category_id', '=', product_uom_category_id)]",
    )
    product_uom_category_id = fields.Many2one(
        related="product_id.uom_id.category_id", readonly=True
    )
    product_uom_readonly = fields.Boolean(compute="_compute_product_uom_readonly")
    product_custom_attribute_value_ids = fields.One2many(
        "product.attribute.custom.value",
        "sale_order_line_id",
        string="Custom Values",
        copy=True,
    )

    qty_to_invoice = fields.Float(
        compute="_compute_get_to_invoice_qty",
        string="To Invoice Quantity",
        store=True,
        readonly=True,
        digits="Product Unit of Measure",
    )
    qty_invoiced = fields.Float(
        compute="_compute_get_invoice_qty",
        string="Invoiced Quantity",
        store=True,
        readonly=True,
        compute_sudo=True,
        digits="Product Unit of Measure",
    )

    untaxed_amount_invoiced = fields.Monetary(
        "Untaxed Invoiced Amount",
        compute="_compute_untaxed_amount_invoiced",
        compute_sudo=True,
        store=True,
    )
    untaxed_amount_to_invoice = fields.Monetary(
        "Untaxed Amount To Invoice",
        compute="_compute_untaxed_amount_to_invoice",
        compute_sudo=True,
        store=True,
    )

    currency_id = fields.Many2one(
        related="folio_id.currency_id",
        depends=["folio_id.currency_id"],
        store=True,
        string="Currency",
        readonly=True,
    )
    company_id = fields.Many2one(
        related="folio_id.company_id",
        string="Company",
        store=True,
        readonly=True,
        index=True,
    )
    folio_partner_id = fields.Many2one(
        related="folio_id.partner_id", store=True, string="Customer", readonly=False
    )
    analytic_tag_ids = fields.Many2many(
        "account.analytic.tag",
        string="Analytic Tags",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    analytic_line_ids = fields.One2many(
        "account.analytic.line", "so_line", string="Analytic lines"
    )
    is_downpayment = fields.Boolean(
        string="Is a down payment",
        help="Down payments are made when creating invoices from a folio."
        " They are not copied when duplicating a folio.",
    )

    state = fields.Selection(
        related="folio_id.state",
        string="Folio Status",
        readonly=True,
        copy=False,
        store=True,
    )

    display_type = fields.Selection(
        [("line_section", "Section"), ("line_note", "Note")],
        default=False,
        help="Technical field for UX purpose.",
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
                    if invoice_line.move_id.move_type == "out_invoice":
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
                        partner=line.folio_id.partner_shipping_id,
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

    def _get_invoice_line_sequence(self, new=0, old=0):
        """
        Method intended to be overridden in third-party
        module if we want to prevent the resequencing of invoice lines.

        :param int new:   the new line sequence
        :param int old:   the old line sequence

        :return:          the sequence of the SO line, by default the new one.
        """
        return new or old

    def _prepare_invoice_line(self, qty=False, **optional_values):
        """
        Prepare the dict of values to create the new invoice line for a folio sale line.

        :param qty: float quantity to invoice
        :param optional_values: any parameter that
            should be added to the returned invoice line
        """
        self.ensure_one()
        if (qty > self.qty_to_invoice or qty < 1) and not self.display_type:
            raise ValueError(
                _(
                    "The qty (%s) is wrong." % qty
                    + " The quantity pending to invoice is %s" % self.qty_to_invoice
                )
            )
        res = {
            "display_type": self.display_type,
            "sequence": self.sequence,
            "name": self.name,
            "product_id": self.product_id.id,
            "product_uom_id": self.product_uom.id,
            "quantity": qty if qty else self.qty_to_invoice,
            "discount": self.discount,
            "price_unit": self.price_unit,
            "tax_ids": [(6, 0, self.tax_ids.ids)],
            "analytic_account_id": self.folio_id.analytic_account_id.id,
            "analytic_tag_ids": [(6, 0, self.analytic_tag_ids.ids)],
            "folio_line_ids": [(6, 0, [self.id])],
        }
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res["account_id"] = False
        return res

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
            "name",
            "price_unit",
            "product_uom",
            "product_uom_qty",
            "tax_ids",
            "analytic_tag_ids",
        ]
