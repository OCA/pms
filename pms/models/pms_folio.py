# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from itertools import groupby

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class PmsFolio(models.Model):
    _name = "pms.folio"
    _description = "PMS Folio"
    _inherit = ["mail.thread", "mail.activity.mixin", "portal.mixin"]
    _order = "date_order"
    _check_company_auto = True
    _check_pms_properties_auto = True

    name = fields.Char(
        string="Folio Number",
        help="Folio name. When creating a folio the "
        "name is automatically formed with a sequence",
        readonly=True,
        index=True,
        default=lambda self: _("New"),
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="The property for folios",
        comodel_name="pms.property",
        required=True,
        default=lambda self: self.env.user.get_active_property_ids()[0],
        check_pms_properties=True,
    )
    partner_id = fields.Many2one(
        string="Partner",
        help="The folio customer",
        readonly=False,
        store=True,
        tracking=True,
        compute="_compute_partner_id",
        comodel_name="res.partner",
        ondelete="restrict",
        check_pms_properties=True,
    )
    reservation_ids = fields.One2many(
        string="Reservations",
        help="Room reservation detail",
        readonly=False,
        states={"done": [("readonly", True)]},
        comodel_name="pms.reservation",
        inverse_name="folio_id",
        check_company=True,
        check_pms_properties=True,
    )
    number_of_rooms = fields.Integer(
        string="Number of Rooms",
        help="Number of rooms in folio. Canceled rooms do not count.",
        store="True",
        compute="_compute_number_of_rooms",
    )
    number_of_cancelled_rooms = fields.Integer(
        string="Number of Cancelled Rooms",
        help="Number of cancelled rooms in folio.",
        store="True",
        compute="_compute_number_of_cancelled_rooms",
    )
    number_of_services = fields.Integer(
        string="Number of Services",
        help="Number of services in the folio",
        store="True",
        compute="_compute_number_of_services",
    )
    service_ids = fields.One2many(
        string="Service",
        help="Services detail provide to customer and it will "
        "include in main Invoice.",
        readonly=False,
        states={"done": [("readonly", True)]},
        comodel_name="pms.service",
        inverse_name="folio_id",
        check_company=True,
        check_pms_properties=True,
    )
    sale_line_ids = fields.One2many(
        string="Sale lines",
        help="Sale lines in folio. It correspond with reservation nights",
        store="True",
        compute="_compute_sale_line_ids",
        compute_sudo=True,
        comodel_name="folio.sale.line",
        inverse_name="folio_id",
    )
    invoice_count = fields.Integer(
        string="Invoice Count",
        help="The amount of invoices in out invoice and out refund status",
        readonly=True,
        compute="_compute_get_invoiced",
    )
    company_id = fields.Many2one(
        string="Company",
        help="The company for folio",
        store=True,
        comodel_name="res.company",
        compute="_compute_company_id",
    )
    move_line_ids = fields.Many2many(
        string="Payments",
        help="Folio payments",
        readonly=True,
        comodel_name="account.move.line",
        relation="payment_folio_rel",
        column1="folio_id",
        column2="move_id",
    )
    analytic_account_id = fields.Many2one(
        string="Analytic Account",
        help="The analytic account related to a folio.",
        readonly=True,
        states={"draft": [("readonly", False)], "sent": [("readonly", False)]},
        copy=False,
        comodel_name="account.analytic.account",
    )
    currency_id = fields.Many2one(
        string="Currency",
        help="The currency of the property location",
        readonly=True,
        required=True,
        related="pricelist_id.currency_id",
        ondelete="restrict",
    )
    pricelist_id = fields.Many2one(
        string="Pricelist",
        help="Pricelist for current folio.",
        readonly=False,
        store=True,
        comodel_name="product.pricelist",
        ondelete="restrict",
        check_pms_properties=True,
        compute="_compute_pricelist_id",
    )
    commission = fields.Float(
        string="Commission",
        readonly=True,
        store=True,
        compute="_compute_commission",
    )
    user_id = fields.Many2one(
        string="Salesperson",
        help="The user who created the folio",
        readonly=False,
        index=True,
        store=True,
        comodel_name="res.users",
        ondelete="restrict",
        compute="_compute_user_id",
        tracking=True,
    )
    agency_id = fields.Many2one(
        string="Agency",
        help="Only allowed if the field of partner is_agency is True",
        comodel_name="res.partner",
        domain=[("is_agency", "=", True)],
        ondelete="restrict",
        check_pms_properties=True,
    )
    channel_type_id = fields.Many2one(
        string="Direct Sale Channel",
        help="Only allowed if the field of sale channel channel_type is 'direct'",
        readonly=False,
        store=True,
        comodel_name="pms.sale.channel",
        domain=[("channel_type", "=", "direct")],
        ondelete="restrict",
        compute="_compute_channel_type_id",
        check_pms_properties=True,
    )
    transaction_ids = fields.Many2many(
        string="Transactions",
        readonly=True,
        copy=False,
        comodel_name="payment.transaction",
        relation="folio_transaction_rel",
        column1="folio_id",
        column2="transaction_id",
    )
    payment_term_id = fields.Many2one(
        string="Payment Terms",
        help="Pricelist for current folio.",
        readonly=False,
        store=True,
        comodel_name="account.payment.term",
        ondelete="restrict",
        compute="_compute_payment_term_id",
    )
    checkin_partner_ids = fields.One2many(
        string="Checkin Partners",
        help="The checkin partners on a folio",
        comodel_name="pms.checkin.partner",
        inverse_name="folio_id",
    )
    count_rooms_pending_arrival = fields.Integer(
        string="Pending Arrival",
        help="The number of rooms left to occupy.",
        store=True,
        compute="_compute_count_rooms_pending_arrival",
    )
    pending_checkin_data = fields.Integer(
        string="Checkin Data",
        compute="_compute_pending_checkin_data",
        store=True,
    )
    ratio_checkin_data = fields.Integer(
        string="Pending Checkin Data",
        help="Field that stores the number of checkin partners pending "
        "to checkin (with the state = draft)",
        compute="_compute_ratio_checkin_data",
    )
    move_ids = fields.Many2many(
        string="Invoices",
        help="Folio invoices related to account move.",
        readonly=True,
        copy=False,
        comodel_name="account.move",
        compute="_compute_get_invoiced",
        search="_search_invoice_ids",
    )
    payment_state = fields.Selection(
        string="Payment Status",
        help="The state of the payment",
        copy=False,
        readonly=True,
        store=True,
        selection=[
            ("not_paid", "Not Paid"),
            ("paid", "Paid"),
            ("partial", "Partially Paid"),
        ],
        compute="_compute_amount",
        tracking=True,
    )
    partner_invoice_ids = fields.Many2many(
        string="Billing addresses",
        help="Invoice address for current group.",
        readonly=False,
        store=True,
        comodel_name="res.partner",
        relation="pms_folio_partner_rel",
        column1="folio",
        column2="partner",
        compute="_compute_partner_invoice_ids",
        check_pms_properties=True,
    )
    # REVIEW THIS
    # partner_invoice_state_id = fields.Many2one(related="partner_invoice_id.state_id")
    # partner_invoice_country_id = fields.Many2one(
    #     related="partner_invoice_id.country_id"
    # )
    fiscal_position_id = fields.Many2one(
        string="Fiscal Position",
        help="The fiscal position depends on the location of the client",
        comodel_name="account.fiscal.position",
    )
    closure_reason_id = fields.Many2one(
        string="Closure Reason",
        help="The closure reason for a closure room",
        comodel_name="room.closure.reason",
        check_pms_properties=True,
    )
    segmentation_ids = fields.Many2many(
        string="Segmentation",
        help="Segmentation tags to classify folios",
        comodel_name="res.partner.category",
        ondelete="restrict",
    )
    client_order_ref = fields.Char(string="Customer Reference", help="", copy=False)
    reservation_type = fields.Selection(
        string="Type",
        help="The type of the reservation. "
        "Can be 'Normal', 'Staff' or 'Out of Service'",
        default=lambda *a: "normal",
        selection=[("normal", "Normal"), ("staff", "Staff"), ("out", "Out of Service")],
    )
    date_order = fields.Datetime(
        string="Order Date",
        help="Date on which folio is sold",
        readonly=True,
        required=True,
        index=True,
        default=fields.Datetime.now,
        states={"draft": [("readonly", False)], "sent": [("readonly", False)]},
        copy=False,
    )
    confirmation_date = fields.Datetime(
        string="Confirmation Date",
        help="Date on which the folio is confirmed.",
        readonly=True,
        index=True,
        copy=False,
    )
    state = fields.Selection(
        string="Status",
        help="Folio status; it can be Quotation, "
        "Quotation Sent, Confirmed, Locked or Cancelled",
        readonly=True,
        index=True,
        default="draft",
        copy=False,
        selection=[
            ("draft", "Quotation"),
            ("sent", "Quotation Sent"),
            ("confirm", "Confirmed"),
            ("done", "Locked"),
            ("cancel", "Cancelled"),
        ],
        tracking=True,
    )
    partner_name = fields.Char(
        string="Customer Name",
        help="In the name of whom the reservation is made",
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
    partner_incongruences = fields.Char(
        string="partner_incongruences",
        help="indicates that some partner fields \
            on the folio do not correspond to that of \
            the associated partner",
        compute="_compute_partner_incongruences",
    )
    partner_internal_comment = fields.Text(
        string="Internal Partner Notes",
        help="Internal notes of the partner",
        related="partner_id.comment",
        store=True,
        readonly=False,
    )
    credit_card_details = fields.Text(
        string="Credit Card Details",
        help="Details of partner credit card",
    )

    pending_amount = fields.Monetary(
        string="Pending Amount",
        help="The amount that remains to be paid",
        store=True,
        compute="_compute_amount",
    )
    # refund_amount = fields.Monetary(
    #     compute="_compute_amount", store=True, string="Payment Returns"
    # )
    invoices_paid = fields.Monetary(
        string="Paid Out",
        help="Amount of invoices paid",
        store=True,
        compute="_compute_amount",
        tracking=True,
    )
    amount_untaxed = fields.Monetary(
        string="Untaxed Amount",
        help="The price without taxes on a folio",
        readonly=True,
        store=True,
        compute="_compute_amount_all",
        tracking=True,
    )
    amount_tax = fields.Monetary(
        string="Taxes",
        help="Price with taxes on a folio",
        readonly=True,
        store=True,
        compute="_compute_amount_all",
    )
    amount_total = fields.Monetary(
        string="Total",
        help="Total amount to be paid",
        readonly=True,
        store=True,
        compute="_compute_amount_all",
        tracking=True,
    )
    max_reservation_priority = fields.Integer(
        string="Max reservation priority on the entire folio",
        help="Max reservation priority on the entire folio",
        compute="_compute_max_reservation_priority",
        store=True,
    )
    invoice_status = fields.Selection(
        string="Invoice Status",
        help="Invoice Status; it can be: upselling, invoiced, to invoice, no",
        readonly=True,
        default="no",
        store=True,
        selection=[
            ("invoiced", "Fully Invoiced"),
            ("to_invoice", "To Invoice"),
            ("no", "Nothing to Invoice"),
        ],
        compute="_compute_get_invoice_status",
        compute_sudo=True,
    )
    internal_comment = fields.Text(
        string="Internal Folio Notes",
        help="Internal Folio notes for Staff",
    )
    cancelled_reason = fields.Text(
        string="Cause of cancelled",
        help="Indicates cause of cancelled",
    )
    prepaid_warning_days = fields.Integer(
        string="Prepaid Warning Days",
        help="Margin in days to create a notice if a payment \
                advance has not been recorded",
    )
    sequence = fields.Integer(
        string="Sequence",
        help="Sequence used to form the name of the folio",
        default=10,
    )
    note = fields.Text(
        string="Terms and conditions",
        help="Folio billing terms and conditions",
        default=lambda self: self._default_note(),
    )
    reference = fields.Char(
        string="Payment Ref.",
        help="The payment communication of this sale order.",
        copy=False,
    )

    def name_get(self):
        result = []
        for folio in self:
            name = folio.name
            if len(folio.reservation_ids) > 1:
                name += " (%s)" % len(folio.reservation_ids)
            result.append((folio.id, name))
        return result

    def _default_note(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("account.use_invoice_terms")
            and self.env.company.invoice_terms
            or ""
        )

    def _get_report_base_filename(self):
        self.ensure_one()
        return "Folio %s" % self.name

    def _get_invoice_grouping_keys(self):
        return ["company_id", "partner_id", "currency_id"]

    def get_invoice_vals_list(
        self, final=False, lines_to_invoice=False, partner_invoice_id=False
    ):
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        invoice_vals_list = []
        invoice_item_sequence = 0
        for order in self:
            order = order.with_company(order.company_id)
            current_section_vals = None
            down_payments = order.env["folio.sale.line"]

            # Invoice values.
            invoice_vals = order._prepare_invoice(partner_invoice_id=partner_invoice_id)

            # Invoice line values (keep only necessary sections).
            invoice_lines_vals = []
            for line in order.sale_line_ids.filtered(
                lambda l: l.id in list(lines_to_invoice.keys())
            ):
                if line.display_type == "line_section":
                    current_section_vals = line._prepare_invoice_line(
                        sequence=invoice_item_sequence + 1
                    )
                    continue
                if line.display_type != "line_note" and float_is_zero(
                    line.qty_to_invoice, precision_digits=precision
                ):
                    continue
                if (
                    line.qty_to_invoice > 0
                    or (line.qty_to_invoice < 0 and final)
                    or line.display_type == "line_note"
                ):
                    if line.is_downpayment:
                        down_payments += line
                        continue
                    if current_section_vals:
                        invoice_item_sequence += 1
                        invoice_lines_vals.append(current_section_vals)
                        current_section_vals = None
                    invoice_item_sequence += 1
                    prepared_line = line._prepare_invoice_line(
                        sequence=invoice_item_sequence, qty=lines_to_invoice[line.id]
                    )
                    invoice_lines_vals.append(prepared_line)

            # If down payments are present in SO, group them under common section
            if down_payments:
                invoice_item_sequence += 1
                down_payments_section = order._prepare_down_payment_section_line(
                    sequence=invoice_item_sequence
                )
                invoice_lines_vals.append(down_payments_section)
                for down_payment in down_payments:
                    invoice_item_sequence += 1
                    invoice_down_payment_vals = down_payment._prepare_invoice_line(
                        sequence=invoice_item_sequence
                    )
                    invoice_lines_vals.append(invoice_down_payment_vals)

            if not any(
                new_line["display_type"] is False for new_line in invoice_lines_vals
            ):
                raise self._nothing_to_invoice_error()

            invoice_vals["invoice_line_ids"] = [
                (0, 0, invoice_line_id) for invoice_line_id in invoice_lines_vals
            ]

            invoice_vals_list.append(invoice_vals)
        return invoice_vals_list

    def _get_tax_amount_by_group(self):
        self.ensure_one()
        res = {}
        for line in self.sale_line_ids:
            price_reduce = line.price_total
            product = line.product_id
            taxes = line.tax_ids.compute_all(price_reduce, quantity=1, product=product)[
                "taxes"
            ]
            for tax in line.tax_ids:
                group = tax.tax_group_id
                res.setdefault(group, {"amount": 0.0, "base": 0.0})
                for t in taxes:
                    if t["id"] == tax.id or t["id"] in tax.children_tax_ids.ids:
                        res[group]["amount"] += t["amount"]
                        res[group]["base"] += t["base"]
        res = sorted(res.items(), key=lambda line: line[0].sequence)
        res = [
            (line[0].name, line[1]["amount"], line[1]["base"], len(res)) for line in res
        ]
        return res

    @api.depends("reservation_ids", "reservation_ids.state")
    def _compute_number_of_rooms(self):
        for folio in self:
            folio.number_of_rooms = len(
                folio.reservation_ids.filtered(lambda a: a.state != "cancel")
            )

    @api.depends("reservation_ids", "reservation_ids.state")
    def _compute_number_of_cancelled_rooms(self):
        for folio in self:
            folio.number_of_cancelled_rooms = len(
                folio.reservation_ids.filtered(lambda a: a.state == "cancel")
            )

    @api.depends("service_ids", "service_ids.product_qty")
    def _compute_number_of_services(self):
        for folio in self:
            folio.number_of_services = sum(folio.service_ids.mapped("product_qty"))

    @api.depends(
        "reservation_ids",
        "service_ids",
        "service_ids.reservation_id",
        "service_ids.service_line_ids.price_day_total",
        "service_ids.service_line_ids.discount",
        "service_ids.service_line_ids.cancel_discount",
        "service_ids.service_line_ids.day_qty",
        "service_ids.service_line_ids.tax_ids",
        "reservation_ids.reservation_line_ids",
        "reservation_ids.reservation_line_ids.price",
        "reservation_ids.reservation_line_ids.discount",
        "reservation_ids.reservation_line_ids.cancel_discount",
        "reservation_ids.tax_ids",
    )
    def _compute_sale_line_ids(self):
        for folio in self:
            for reservation in folio.reservation_ids:
                # RESERVATION LINES
                # res = self.env['pms.reservation'].browse(reservation.id)
                self.generate_reservation_lines_sale_lines(folio, reservation)

                # RESERVATION SERVICES
                self.generate_reservation_services_sale_lines(folio, reservation)

            # FOLIO SERVICES
            self.generate_folio_services_sale_lines(folio)

    @api.depends("pms_property_id")
    def _compute_company_id(self):
        for record in self:
            record.company_id = record.pms_property_id.company_id

    @api.depends(
        "partner_id", "agency_id", "reservation_ids", "reservation_ids.pricelist_id"
    )
    def _compute_pricelist_id(self):
        for folio in self:
            if len(folio.reservation_ids.pricelist_id) == 1:
                folio.pricelist_id = folio.reservation_ids.pricelist_id
            elif folio.agency_id and folio.agency_id.apply_pricelist:
                folio.pricelist_id = folio.agency_id.property_product_pricelist
            elif folio.partner_id and folio.partner_id.property_product_pricelist:
                folio.pricelist_id = folio.partner_id.property_product_pricelist
            elif not folio.pricelist_id:
                folio.pricelist_id = folio.pms_property_id.default_pricelist_id

    @api.depends("agency_id")
    def _compute_partner_id(self):
        for folio in self:
            if folio.agency_id and folio.agency_id.invoice_to_agency:
                folio.partner_id = folio.agency_id.id
            elif not folio.partner_id:
                folio.partner_id = False

    @api.depends("partner_id")
    def _compute_user_id(self):
        for folio in self:
            if not folio.user_id:
                folio.user_id = (folio.partner_id.user_id.id or self.env.uid,)

    @api.depends("partner_id")
    def _compute_partner_invoice_ids(self):
        for folio in self.filtered("partner_id"):
            folio.partner_invoice_ids = False
            addr = folio.partner_id.address_get(["invoice"])
            if not addr["invoice"] in folio.partner_invoice_ids.ids:
                folio.partner_invoice_ids = [(4, addr["invoice"])]
        # Avoid CacheMissing
        self.filtered(lambda f: not f.partner_invoice_ids).partner_invoice_ids = False

    @api.depends("partner_id")
    def _compute_payment_term_id(self):
        self.payment_term_id = False
        for folio in self:
            folio.payment_term_id = (
                folio.partner_id.property_payment_term_id
                and folio.partner_id.property_payment_term_id.id
                or False
            )

    @api.depends("reservation_ids", "reservation_ids.commission_amount")
    def _compute_commission(self):
        for folio in self:
            for reservation in folio.reservation_ids:
                if reservation.commission_amount != 0:
                    folio.commission += reservation.commission_amount
                else:
                    folio.commission = 0

    @api.depends("agency_id")
    def _compute_channel_type_id(self):
        for folio in self:
            if folio.agency_id:
                folio.channel_type_id = folio.agency_id.sale_channel_id.id

    @api.depends("sale_line_ids.invoice_lines")
    def _compute_get_invoiced(self):
        # The invoice_ids are obtained thanks to the invoice lines of the SO
        # lines, and we also search for possible refunds created directly from
        # existing invoices. This is necessary since such a refund is not
        # directly linked to the SO.
        for order in self:
            invoices = order.sale_line_ids.invoice_lines.move_id.filtered(
                lambda r: r.move_type in ("out_invoice", "out_refund")
            )
            order.move_ids = invoices
            order.invoice_count = len(invoices)

    # @api.depends(
    #     "reservation_ids",
    #     "reservation_ids.currency_id"
    # )
    # def _compute_currency_id(self):
    #     if len(self.reservation_ids.mapped("currency_id")) == 1:
    #         self.currency_id = self.reservation_ids.mapped("currency_id")
    #     else:
    #         raise UserError(_("Some reservations have different currency"))

    def _compute_access_url(self):
        super(PmsFolio, self)._compute_access_url()
        for folio in self:
            folio.access_url = "/my/folios/%s" % (folio.id)

    @api.depends("state", "sale_line_ids.invoice_status")
    def _compute_get_invoice_status(self):
        """
        Compute the invoice status of a Folio. Possible statuses:
        - no: if the Folio is in status 'draft', we consider that there is nothing to
          invoice. This is also the default value if the conditions of no
          other status is met.
        - to_invoice: if any SO line is 'to_invoice', the whole SO is 'to_invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        """
        unconfirmed_orders = self.filtered(lambda so: so.state in ["draft"])
        unconfirmed_orders.invoice_status = "no"
        confirmed_orders = self - unconfirmed_orders
        if not confirmed_orders:
            return
        line_invoice_status_all = [
            (d["folio_id"][0], d["invoice_status"])
            for d in self.env["folio.sale.line"].read_group(
                [
                    ("folio_id", "in", confirmed_orders.ids),
                    ("is_downpayment", "=", False),
                    ("display_type", "=", False),
                ],
                ["folio_id", "invoice_status"],
                ["folio_id", "invoice_status"],
                lazy=False,
            )
        ]
        for order in confirmed_orders:
            line_invoice_status = [
                d[1] for d in line_invoice_status_all if d[0] == order.id
            ]
            if order.state in ("draft"):
                order.invoice_status = "no"
            elif any(
                invoice_status == "to_invoice" for invoice_status in line_invoice_status
            ):
                order.invoice_status = "to_invoice"
            elif line_invoice_status and all(
                invoice_status == "invoiced" for invoice_status in line_invoice_status
            ):
                order.invoice_status = "invoiced"
            elif line_invoice_status and all(
                invoice_status in ("invoiced", "upselling")
                for invoice_status in line_invoice_status
            ):
                order.invoice_status = "upselling"
            else:
                order.invoice_status = "no"

    @api.depends("partner_id", "partner_id.name")
    def _compute_partner_name(self):
        for record in self:
            self._apply_partner_name(record)

    @api.depends("partner_id", "partner_id.email")
    def _compute_email(self):
        for record in self:
            self._apply_email(record)

    @api.depends("partner_id", "partner_id.mobile")
    def _compute_mobile(self):
        for record in self:
            self._apply_mobile(record)

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

    @api.depends("sale_line_ids.price_total")
    def _compute_amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for folio in self:
            amount_untaxed = amount_tax = 0.0
            for line in folio.sale_line_ids:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            folio.update(
                {
                    "amount_untaxed": amount_untaxed,
                    "amount_tax": amount_tax,
                    "amount_total": amount_untaxed + amount_tax,
                }
            )

    @api.depends("reservation_ids", "reservation_ids.state")
    def _compute_count_rooms_pending_arrival(self):
        self.count_rooms_pending_arrival = 0
        for folio in self.filtered("reservation_ids"):
            folio.count_rooms_pending_arrival = len(
                folio.reservation_ids.filtered(
                    lambda c: c.state in ("draf", "confirm", "arrival_delayed")
                )
            )

    @api.depends("checkin_partner_ids", "checkin_partner_ids.state")
    def _compute_pending_checkin_data(self):
        for folio in self:
            folio.pending_checkin_data = len(
                folio.checkin_partner_ids.filtered(lambda c: c.state == "draft")
            )

    @api.depends("pending_checkin_data")
    def _compute_ratio_checkin_data(self):
        self.ratio_checkin_data = 0
        for folio in self.filtered("reservation_ids"):
            folio.ratio_checkin_data = (
                (
                    sum(folio.reservation_ids.mapped("adults"))
                    - folio.pending_checkin_data
                )
                * 100
                / sum(folio.reservation_ids.mapped("adults"))
            )

    # TODO: Add return_ids to depends
    @api.depends(
        "amount_total",
        "reservation_type",
        "state",
        "move_line_ids",
        "move_line_ids.parent_state",
        "sale_line_ids.invoice_lines",
        "sale_line_ids.invoice_lines.move_id.payment_state",
    )
    def _compute_amount(self):
        for record in self:
            if record.reservation_type in ("staff", "out"):
                vals = {
                    "pending_amount": 0,
                    "invoices_paid": 0,
                }
                record.update(vals)
            else:
                journals = record.pms_property_id._get_payment_methods()
                paid_out = 0
                for journal in journals:
                    paid_out += sum(
                        self.env["account.move.line"]
                        .search(
                            [
                                ("folio_ids", "in", record.id),
                                (
                                    "account_id",
                                    "in",
                                    tuple(
                                        journal.default_account_id.ids
                                        + journal.payment_debit_account_id.ids
                                        + journal.payment_credit_account_id.ids
                                    ),
                                ),
                                (
                                    "display_type",
                                    "not in",
                                    ("line_section", "line_note"),
                                ),
                                ("move_id.state", "!=", "cancel"),
                            ]
                        )
                        .mapped("balance")
                    )
                total = record.amount_total
                # REVIEW: Must We ignored services in cancelled folios
                # pending amount?
                if record.state == "cancel":
                    total = total - sum(record.service_ids.mapped("price_total"))
                # Compute 'payment_state'.
                if total <= paid_out:
                    payment_state = "paid"
                elif paid_out <= 0:
                    payment_state = "not_paid"
                else:
                    payment_state = "partial"
                vals = {
                    "pending_amount": total - paid_out,
                    "invoices_paid": paid_out,
                    "payment_state": payment_state,
                }
                record.update(vals)

    @api.depends("reservation_ids", "reservation_ids.priority")
    def _compute_max_reservation_priority(self):
        for record in self.filtered("reservation_ids"):
            reservation_priors = record.reservation_ids.mapped("priority")
            record.max_reservation_priority = max(reservation_priors)

    def _compute_checkin_partner_count(self):
        for record in self:
            if record.reservation_type == "normal" and record.reservation_ids:
                filtered_reservs = record.reservation_ids.filtered(
                    lambda x: x.state != "cancel"
                )
                mapped_checkin_partner = filtered_reservs.mapped(
                    "checkin_partner_ids.id"
                )
                record.checkin_partner_count = len(mapped_checkin_partner)
                mapped_checkin_partner_count = filtered_reservs.mapped(
                    lambda x: (x.adults + x.children) - len(x.checkin_partner_ids)
                )
                record.checkin_partner_pending_count = sum(mapped_checkin_partner_count)

    def _search_invoice_ids(self, operator, value):
        if operator == "in" and value:
            self.env.cr.execute(
                """
                SELECT array_agg(so.id)
                    FROM pms_folio so
                    JOIN folio_sale_line sol ON sol.folio_id = so.id
                    JOIN folio_sale_line_invoice_rel soli_rel ON \
                        soli_rel.sale_line_ids = sol.id
                    JOIN account_move_line aml ON aml.id = soli_rel.invoice_line_id
                    JOIN account_move am ON am.id = aml.move_id
                WHERE
                    am.move_type in ('out_invoice', 'out_refund') AND
                    am.id = ANY(%s)
            """,
                (list(value),),
            )
            so_ids = self.env.cr.fetchone()[0] or []
            return [("id", "in", so_ids)]
        return [
            "&",
            (
                "sale_line_ids.invoice_lines.move_id.move_type",
                "in",
                ("out_invoice", "out_refund"),
            ),
            ("sale_line_ids.invoice_lines.move_id", operator, value),
        ]

    @api.constrains("agency_id", "channel_type_id")
    def _check_only_one_channel(self):
        for record in self:
            if (
                record.agency_id
                and record.channel_type_id.channel_type
                != record.agency_id.sale_channel_id.channel_type
            ):
                raise models.ValidationError(
                    _("The Sale Channel does not correspond to the agency's")
                )

    @api.constrains("name")
    def _check_required_partner_name(self):
        for record in self:
            if not record.partner_name:
                raise models.ValidationError(_("You must assign a customer name"))

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New") or "name" not in vals:
            pms_property_id = (
                self.env.user.get_active_property_ids()[0]
                if "pms_property_id" not in vals
                else vals["pms_property_id"]
            )
            pms_property = self.env["pms.property"].browse(pms_property_id)
            vals["name"] = pms_property.folio_sequence_id._next_do()
        result = super(PmsFolio, self).create(vals)
        return result

    def action_pay(self):
        self.ensure_one()
        self.ensure_one()
        partner = self.partner_id.id
        amount = self.pending_amount
        view_id = self.env.ref("pms.wizard_payment_folio_view_form").id
        return {
            "name": _("Register Payment"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "wizard.payment.folio",
            "type": "ir.actions.act_window",
            "view_id": view_id,
            "context": {
                "default_folio_id": self.id,
                "default_amount": amount,
                "default_partner_id": partner,
            },
            "target": "new",
        }

    def open_partner(self):
        """ Utility method used to add an "View Customer" button in folio views """
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

    def open_moves_folio(self):
        invoices = self.mapped("move_ids")
        action = self.env.ref("account.action_move_out_invoice_type").sudo().read()[0]
        if len(invoices) > 1:
            action["domain"] = [("id", "in", invoices.ids)]
        elif len(invoices) == 1:
            action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
            action["res_id"] = invoices.ids[0]
        else:
            action = {"type": "ir.actions.act_window_close"}
        return action

    def folio_multi_changes(self):
        self.ensure_one()
        reservation_ids = self.reservation_ids.ids
        action = self.env.ref("pms.action_folio_changes").sudo().read()[0]
        action["context"] = ({"default_reservation_ids": [(6, 0, reservation_ids)]},)
        return action

    # def action_return_payments(self):
    #     self.ensure_one()
    #     return_move_ids = []
    #     acc_pay_obj = self.env["account.payment"]
    #     payments = acc_pay_obj.search(
    #         ["|", ("move_ids", "in", self.move_ids.ids), ("folio_id", "=", self.id)]
    #     )
    #     return_move_ids += self.move_ids.filtered(
    #         lambda invoice: invoice.type == "out_refund"
    #     ).mapped("payment_move_line_ids.move_id.id")
    #     return_lines = self.env["payment.return.line"].search(
    #         [("move_line_ids", "in", payments.mapped("move_line_ids.id")),]
    #     )
    #     return_move_ids += return_lines.mapped("return_id.move_id.id")

    #     return {
    #         "name": _("Returns"),
    #         "view_type": "form",
    #         "view_mode": "tree,form",
    #         "res_model": "account.move",
    #         "type": "ir.actions.act_window",
    #         "domain": [("id", "in", return_move_ids)],
    #     }

    def action_checks(self):
        self.ensure_one()
        rooms = self.mapped("reservation_ids.id")
        return {
            "name": _("Checkins"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "pms.checkin.partner",
            "type": "ir.actions.act_window",
            "domain": [("reservation_id", "in", rooms)],
            "search_view_id": [
                self.env.ref("pms.pms_checkin_partner_view_folio_search").id,
                "search",
            ],
            "target": "new",
        }

    def action_to_arrive(self):
        self.ensure_one()
        reservations = self.reservation_ids.filtered(
            lambda c: c.state in ("draf", "confirm", "arrival_delayed")
        )
        action = self.env.ref("pms.open_pms_reservation_form_tree_all").read()[0]
        action["domain"] = [("id", "in", reservations.ids)]
        return action

    def action_done(self):
        reservation_ids = self.mapped("reservation_ids")
        for line in reservation_ids:
            if line.state == "onboard":
                line.action_reservation_checkout()

    def action_cancel(self):
        for folio in self:
            for reservation in folio.reservation_ids.filtered(
                lambda res: res.state != "cancel"
            ):
                reservation.action_cancel()
            self.write(
                {
                    "state": "cancel",
                }
            )
        return True

    def action_confirm(self):
        self.filtered(lambda x: x.state != "confirm").write(
            {"state": "confirm", "confirmation_date": fields.Datetime.now()}
        )

        if self.env.context.get("confirm_all_reservations"):
            self.reservation_ids.confirm()

        # if self.env.context.get('send_email'):
        # self.force_quotation_send()

        # create an analytic account if at least an expense product
        # if any([expense_policy != 'no' for expense_policy in
        # self.sale_line_ids.mapped('product_id.expense_policy')]):
        # if not self.analytic_account_id:
        # self._create_analytic_account()
        return True

    # CHECKIN/OUT PROCESS

    def action_view_invoice(self):
        invoices = self.mapped("move_ids")
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_out_invoice_type"
        )
        if len(invoices) > 1:
            action["domain"] = [("id", "in", invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref("account.view_move_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = invoices.id
        else:
            action = {"type": "ir.actions.act_window_close"}

        context = {
            "default_move_type": "out_invoice",
        }
        if len(self) == 1:
            context.update(
                {
                    "default_partner_id": self.partner_id.id,
                    "default_invoice_payment_term_id": self.payment_term_id.id
                    or self.partner_id.property_payment_term_id.id
                    or self.env["account.move"]
                    .default_get(["invoice_payment_term_id"])
                    .get("invoice_payment_term_id"),
                    "default_invoice_origin": self.mapped("name"),
                    "default_user_id": self.user_id.id,
                }
            )
        action["context"] = context
        return action

    def preview_folio(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "target": "self",
            "url": self.get_portal_url(),
        }

    def _create_invoices(
        self,
        grouped=False,
        final=False,
        date=None,
        lines_to_invoice=False,
        partner_invoice_id=False,
    ):
        """
        Create the invoice associated to the Folio.
        :param grouped: if True, invoices are grouped by Folio id.
        If False, invoices are grouped by
                        (partner_invoice_ids, currency)
        :param final: if True, refunds will be generated if necessary
        :param lines_to_invoice: invoice specific lines dict(key=id, value=qty).
            if False, invoice all
        :returns: list of created invoices
        """
        if not self.env["account.move"].check_access_rights("create", False):
            try:
                self.check_access_rights("write")
                self.check_access_rule("write")
            except AccessError:
                return self.env["account.move"]
        # 1) Create invoices.
        if not lines_to_invoice:
            lines_to_invoice = dict()
            for line in self.sale_line_ids:
                lines_to_invoice[line.id] = (
                    0 if line.display_type else line.qty_to_invoice
                )
        invoice_vals_list = self.get_invoice_vals_list(
            final=final,
            lines_to_invoice=lines_to_invoice,
            partner_invoice_id=partner_invoice_id,
        )

        if not invoice_vals_list:
            raise self._nothing_to_invoice_error()

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            for _grouping_keys, invoices in groupby(
                invoice_vals_list,
                key=lambda x: [
                    x.get(grouping_key) for grouping_key in invoice_grouping_keys
                ],
            ):
                origins = set()
                payment_refs = set()
                refs = set()
                ref_invoice_vals = None
                for invoice_vals in invoices:
                    if not ref_invoice_vals:
                        ref_invoice_vals = invoice_vals
                    else:
                        ref_invoice_vals["invoice_line_ids"] += invoice_vals[
                            "invoice_line_ids"
                        ]
                    origins.add(invoice_vals["invoice_origin"])
                    payment_refs.add(invoice_vals["payment_reference"])
                    refs.add(invoice_vals["ref"])
                ref_invoice_vals.update(
                    {
                        "ref": ", ".join(refs)[:2000],
                        "invoice_origin": ", ".join(origins),
                        "payment_reference": len(payment_refs) == 1
                        and payment_refs.pop()
                        or False,
                    }
                )
                new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.

        # As part of the invoice creation, we make sure the
        # sequence of multiple SO do not interfere
        # in a single invoice. Example:
        # Folio 1:
        # - Section A (sequence: 10)
        # - Product A (sequence: 11)
        # Folio 2:
        # - Section B (sequence: 10)
        # - Product B (sequence: 11)
        #
        # If Folio 1 & 2 are grouped in the same invoice,
        # the result will be:
        # - Section A (sequence: 10)
        # - Section B (sequence: 10)
        # - Product A (sequence: 11)
        # - Product B (sequence: 11)
        #
        # Resequencing should be safe, however we resequence only
        # if there are less invoices than orders, meaning a grouping
        # might have been done. This could also mean that only a part
        # of the selected SO are invoiceable, but resequencing
        # in this case shouldn't be an issue.
        if len(invoice_vals_list) < len(self):
            FolioSaleLine = self.env["folio.sale.line"]
            for invoice in invoice_vals_list:
                sequence = 1
                for line in invoice["invoice_line_ids"]:
                    line[2]["sequence"] = FolioSaleLine._get_invoice_line_sequence(
                        new=sequence, old=line[2]["sequence"]
                    )
                    sequence += 1

        # Manage the creation of invoices in sudo because
        # a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights.
        # However, he should not be able to create an invoice from scratch.
        moves = (
            self.env["account.move"]
            .sudo()
            .with_context(default_move_type="out_invoice", auto_name=True)
            .create(invoice_vals_list)
        )

        # 4) Some moves might actually be refunds: convert
        # them if the total amount is negative
        # We do this after the moves have been created
        # since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(
                lambda m: m.amount_total < 0
            ).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view(
                "mail.message_origin_link",
                values={
                    "self": move,
                    "origin": move.line_ids.mapped("folio_line_ids.folio_id"),
                },
                subtype_id=self.env.ref("mail.mt_note").id,
            )
        return moves

    def _prepare_invoice(self, partner_invoice_id=False):
        """
        Prepare the dict of values to create the new invoice for a folio.
        This method may be overridden to implement custom invoice generation
        (making sure to call super() to establish a clean extension chain).
        """
        self.ensure_one()
        journal = (
            self.env["account.move"]
            .with_context(default_move_type="out_invoice")
            ._get_default_journal()
        )
        if not journal:
            raise UserError(
                _("Please define an accounting sales journal for the company %s (%s).")
                % (self.company_id.name, self.company_id.id)
            )

        invoice_vals = {
            "ref": self.client_order_ref or "",
            "move_type": "out_invoice",
            "narration": self.note,
            "currency_id": self.pricelist_id.currency_id.id,
            # 'campaign_id': self.campaign_id.id,
            # 'medium_id': self.medium_id.id,
            # 'source_id': self.source_id.id,
            "invoice_user_id": self.user_id and self.user_id.id,
            "partner_id": partner_invoice_id
            if partner_invoice_id
            else self.partner_invoice_ids[0],
            "partner_bank_id": self.company_id.partner_id.bank_ids[:1].id,
            "journal_id": journal.id,  # company comes from the journal
            "invoice_origin": self.name,
            "invoice_payment_term_id": self.payment_term_id.id,
            "payment_reference": self.reference,
            "transaction_ids": [(6, 0, self.transaction_ids.ids)],
            "folio_ids": [(6, 0, [self.id])],
            "invoice_line_ids": [],
            "company_id": self.company_id.id,
        }
        return invoice_vals

    def do_payment(
        self,
        journal,
        receivable_account,
        user,
        amount,
        folio,
        reservations=False,
        services=False,
        partner=False,
        date=False,
    ):
        line = self._get_statement_line_vals(
            journal=journal,
            receivable_account=receivable_account,
            user=user,
            amount=amount,
            folios=folio,
            reservations=reservations,
            services=services,
            partner=partner,
            date=date,
        )
        self.env["account.bank.statement.line"].sudo().create(line)

    @api.model
    def _get_statement_line_vals(
        self,
        journal,
        receivable_account,
        user,
        amount,
        folios,
        reservations=False,
        services=False,
        partner=False,
        date=False,
    ):
        property_folio_id = folios.mapped("pms_property_id.id")
        if len(property_folio_id) != 1:
            raise ValidationError(_("Only can payment by property"))
        ctx = dict(self.env.context, company_id=folios[0].company_id.id)
        statement = (
            self.env["account.bank.statement"]
            .sudo()
            .search(
                [
                    ("journal_id", "=", journal.id),
                    ("pms_property_id", "=", property_folio_id[0]),
                    ("state", "=", "open"),
                ]
            )
        )
        reservation_ids = reservations.ids if reservations else []
        service_ids = services.ids if services else []
        if not statement:
            # TODO: cash control option
            st_values = {
                "journal_id": journal.id,
                "user_id": self.env.user.id,
                "pms_property_id": property_folio_id[0],
                "name": str(fields.Datetime.now()),
            }
            statement = (
                self.env["account.bank.statement"]
                .with_context(ctx)
                .sudo()
                .create(st_values)
            )
        return {
            "date": date,
            "amount": amount,
            "partner_id": partner.id if partner else False,
            "folio_ids": [(6, 0, folios.ids)],
            "reservation_ids": [(6, 0, reservation_ids)],
            "service_ids": [(6, 0, service_ids)],
            "payment_ref": folios.mapped("name"),
            "statement_id": statement.id,
            "journal_id": statement.journal_id.id,
            "counterpart_account_id": receivable_account.id,
        }

    @api.model
    def generate_reservation_lines_sale_lines(self, folio, reservation):
        if not reservation.sale_line_ids.filtered(lambda x: x.name == reservation.name):
            reservation.sale_line_ids = [
                (
                    0,
                    0,
                    {
                        "name": reservation.name,
                        "display_type": "line_section",
                        "folio_id": folio.id,
                    },
                )
            ]
        expected_reservation_lines = self.env["pms.reservation.line"].read_group(
            [
                ("reservation_id", "=", reservation.id),
                ("cancel_discount", "<", 100),
            ],
            ["price", "discount", "cancel_discount"],
            ["price", "discount", "cancel_discount"],
            lazy=False,
        )
        current_sale_line_ids = reservation.sale_line_ids.filtered(
            lambda x: x.reservation_id.id == reservation.id
            and not x.display_type
            and not x.service_id
        )

        for index, item in enumerate(expected_reservation_lines):
            lines_to = self.env["pms.reservation.line"].search(item["__domain"])
            final_discount = self.concat_discounts(
                item["discount"], item["cancel_discount"]
            )

            if current_sale_line_ids and index <= (len(current_sale_line_ids) - 1):
                current_sale_line_ids[index].price_unit = item["price"]
                current_sale_line_ids[index].discount = final_discount
                current_sale_line_ids[index].reservation_line_ids = lines_to.ids
            else:
                new = {
                    "reservation_id": reservation.id,
                    "price_unit": item["price"],
                    "discount": final_discount,
                    "folio_id": folio.id,
                    "reservation_line_ids": [(6, 0, lines_to.ids)],
                }
                reservation.sale_line_ids = [(0, 0, new)]
        if len(expected_reservation_lines) < len(current_sale_line_ids):
            folio_sale_lines_to_remove = [
                value.id
                for index, value in enumerate(current_sale_line_ids)
                if index > (len(expected_reservation_lines) - 1)
            ]
            for fsl in folio_sale_lines_to_remove:
                self.env["folio.sale.line"].browse(fsl).unlink()

    @api.model
    def _prepare_down_payment_section_line(self, **optional_values):
        """
        Prepare the dict of values to create a new down
        payment section for a sales order line.
        :param optional_values: any parameter that should
        be added to the returned down payment section
        """
        down_payments_section_line = {
            "display_type": "line_section",
            "name": _("Down Payments"),
            "product_id": False,
            "product_uom_id": False,
            "quantity": 0,
            "discount": 0,
            "price_unit": 0,
            "account_id": False,
        }
        if optional_values:
            down_payments_section_line.update(optional_values)
        return down_payments_section_line

    @api.model
    def _nothing_to_invoice_error(self):
        msg = _(
            """There is nothing to invoice!\n
        Reason(s) of this behavior could be:
        - You should deliver your products before invoicing them: Click on the "truck"
        icon (top-right of your screen) and follow instructions.
        - You should modify the invoicing policy of your product: Open the product,
        go to the "Sales tab" and modify invoicing policy from "delivered quantities"
        to "ordered quantities".
        """
        )
        return UserError(msg)

    @api.model
    def generate_reservation_services_sale_lines(self, folio, reservation):
        for service in reservation.service_ids:
            expected_reservation_services = self.env["pms.service.line"].read_group(
                [
                    ("reservation_id", "=", reservation.id),
                    ("service_id", "=", service.id),
                    ("cancel_discount", "<", 100),
                ],
                ["price_unit", "discount", "cancel_discount"],
                ["price_unit", "discount", "cancel_discount"],
                lazy=False,
            )
            current_sale_service_ids = reservation.sale_line_ids.filtered(
                lambda x: x.reservation_id.id == reservation.id
                and not x.display_type
                and x.service_id.id == service.id
            )

            for index, item in enumerate(expected_reservation_services):
                lines_to = self.env["pms.service.line"].search(item["__domain"])
                final_discount = self.concat_discounts(
                    item["discount"], item["cancel_discount"]
                )

                if current_sale_service_ids and index <= (
                    len(current_sale_service_ids) - 1
                ):
                    current_sale_service_ids[index].price_unit = item["price_unit"]
                    current_sale_service_ids[index].discount = final_discount
                    current_sale_service_ids[index].service_line_ids = lines_to.ids
                else:
                    new = {
                        "service_id": service.id,
                        "price_unit": item["price_unit"],
                        "discount": final_discount,
                        "folio_id": folio.id,
                        "service_line_ids": [(6, 0, lines_to.ids)],
                    }
                    reservation.sale_line_ids = [(0, 0, new)]
            if len(expected_reservation_services) < len(current_sale_service_ids):
                folio_sale_lines_to_remove = [
                    value.id
                    for index, value in enumerate(current_sale_service_ids)
                    if index > (len(expected_reservation_services) - 1)
                ]
                for fsl in folio_sale_lines_to_remove:
                    self.env["folio.sale.line"].browse(fsl).unlink()

    @api.model
    def generate_folio_services_sale_lines(self, folio):
        folio_services = folio.service_ids.filtered(lambda x: not x.reservation_id)
        if folio_services:
            if not folio.sale_line_ids.filtered(lambda x: x.name == _("Others")):
                folio.sale_line_ids = [
                    (
                        0,
                        False,
                        {
                            "display_type": "line_section",
                            "name": _("Others"),
                        },
                    )
                ]
            for folio_service in folio_services:
                expected_folio_services = self.env["pms.service.line"].read_group(
                    [
                        ("service_id.folio_id", "=", folio.id),
                        ("service_id", "=", folio_service.id),
                        ("reservation_id", "=", False),
                        ("cancel_discount", "<", 100),
                    ],
                    ["price_unit", "discount", "cancel_discount"],
                    ["price_unit", "discount", "cancel_discount"],
                    lazy=False,
                )
                current_folio_service_ids = folio.sale_line_ids.filtered(
                    lambda x: x.service_id.folio_id.id == folio.id
                    and not x.display_type
                    and not x.reservation_id
                    and x.service_id.id == folio_service.id
                )

                for index, item in enumerate(expected_folio_services):
                    lines_to = self.env["pms.service.line"].search(item["__domain"])
                    final_discount = self.concat_discounts(
                        item["discount"], item["cancel_discount"]
                    )
                    if current_folio_service_ids and index <= (
                        len(current_folio_service_ids) - 1
                    ):
                        current_folio_service_ids[index].price_unit = item["price_unit"]
                        current_folio_service_ids[index].discount = final_discount
                        current_folio_service_ids[index].service_line_ids = lines_to.ids
                    else:
                        new = {
                            "service_id": folio_service.id,
                            "price_unit": item["price_unit"],
                            "discount": final_discount,
                            "folio_id": folio.id,
                            "service_line_ids": [(6, 0, lines_to.ids)],
                        }
                        folio.sale_line_ids = [(0, 0, new)]
                if len(expected_folio_services) < len(current_folio_service_ids):
                    folio_sale_lines_to_remove = [
                        value.id
                        for index, value in enumerate(current_folio_service_ids)
                        if index > (len(expected_folio_services) - 1)
                    ]
                    for fsl in folio_sale_lines_to_remove:
                        self.env["folio.sale.line"].browse(fsl).unlink()
        else:
            to_unlink = folio.sale_line_ids.filtered(lambda x: x.name == _("Others"))
            to_unlink.unlink()

    @api.model
    def concat_discounts(self, discount, cancel_discount):
        discount_factor = 1.0
        for discount in [discount, cancel_discount]:
            discount_factor = discount_factor * ((100.0 - discount) / 100.0)
        final_discount = 100.0 - (discount_factor * 100.0)
        return final_discount

    @api.model
    def _apply_partner_name(self, record):
        if record.partner_id and not record.partner_name:
            record.partner_name = record.partner_id.name
        elif (
            record.agency_id
            and not record.agency_id.invoice_to_agency
            and not record.partner_name
        ):
            # if the customer not is the agency but we dont know the customer's name,
            # set the name provisional
            record.partner_name = _("Reservation from ") + record.agency_id.name
        elif not record.partner_name:
            record.partner_name = False

    @api.model
    def _apply_mobile(self, record):
        if record.partner_id and not record.mobile:
            record.mobile = record.partner_id.mobile
        elif not record.mobile:
            record.mobile = False

    @api.model
    def _apply_email(self, record):
        if record.partner_id and not record.email:
            record.email = record.partner_id.email
        elif not record.email:
            record.email = False
