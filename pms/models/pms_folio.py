# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime
import logging
from itertools import groupby

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare, float_is_zero

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
    external_reference = fields.Char(
        help="Reference of this folio in an external system",
        compute="_compute_external_reference",
        readonly=False,
        store=True,
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="The property for folios",
        comodel_name="pms.property",
        required=True,
        index=True,
        check_pms_properties=True,
    )
    partner_id = fields.Many2one(
        string="Partner",
        help="The folio customer",
        readonly=False,
        store=True,
        tracking=True,
        index=True,
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
        help="Number of rooms in folio. Canceled rooms do not count.",
        store="True",
        compute="_compute_number_of_rooms",
    )
    number_of_cancelled_rooms = fields.Integer(
        help="Number of cancelled rooms in folio.",
        store="True",
        compute="_compute_number_of_cancelled_rooms",
    )
    number_of_services = fields.Integer(
        help="Number of services in the folio",
        store="True",
        compute="_compute_number_of_services",
    )
    service_ids = fields.One2many(
        string="Services",
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
        help="The amount of invoices in out invoice and out refund status",
        readonly=True,
        compute="_compute_get_invoiced",
    )
    company_id = fields.Many2one(
        string="Company",
        help="The company for folio",
        store=True,
        index=True,
        comodel_name="res.company",
        compute="_compute_company_id",
    )
    analytic_account_id = fields.Many2one(
        string="Analytic Account",
        help="The analytic account related to a folio.",
        readonly=True,
        index=True,
        states={"draft": [("readonly", False)], "sent": [("readonly", False)]},
        copy=False,
        comodel_name="account.analytic.account",
    )
    currency_id = fields.Many2one(
        related="pricelist_id.currency_id",
        depends=["pricelist_id"],
        store=True,
        ondelete="restrict",
    )
    pricelist_id = fields.Many2one(
        string="Pricelist",
        help="Pricelist for current folio.",
        readonly=False,
        store=True,
        index=True,
        comodel_name="product.pricelist",
        ondelete="restrict",
        check_pms_properties=True,
        compute="_compute_pricelist_id",
    )
    commission = fields.Float(
        readonly=True,
        store=True,
        compute="_compute_commission",
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
    revenue_user_id = fields.Many2one(
        string="Revenue Manager",
        help="The revenue manager in the folio",
        readonly=False,
        index=True,
        store=True,
        comodel_name="res.users",
        ondelete="restrict",
        compute="_compute_revenue_user_id",
        tracking=True,
    )
    administrative_user_id = fields.Many2one(
        string="Administrative Manager",
        help="The administrative manager in the folio",
        readonly=False,
        index=True,
        store=True,
        comodel_name="res.users",
        ondelete="restrict",
        compute="_compute_administrative_user_id",
        tracking=True,
    )
    manager_user_id = fields.Many2one(
        string="Main Manager",
        help="The main manager in the folio",
        readonly=False,
        index=True,
        store=True,
        comodel_name="res.users",
        ondelete="restrict",
        compute="_compute_manager_user_id",
        tracking=True,
    )
    agency_id = fields.Many2one(
        string="Agency",
        help="Only allowed if the field of partner is_agency is True",
        comodel_name="res.partner",
        domain=[("is_agency", "=", True)],
        ondelete="restrict",
        index=True,
        check_pms_properties=True,
    )
    sale_channel_ids = fields.Many2many(
        string="Sale Channels",
        help="Sale Channels through which reservations were managed",
        store=True,
        compute="_compute_sale_channel_ids",
        comodel_name="pms.sale.channel",
    )
    sale_channel_origin_id = fields.Many2one(
        string="Sale Channel Origin",
        help="Sale Channel through which folio was created, the original",
        comodel_name="pms.sale.channel",
        index=True,
    )

    transaction_ids = fields.Many2many(
        string="Transactions",
        help="Payments made through payment acquirer",
        readonly=True,
        copy=False,
        comodel_name="payment.transaction",
        relation="payment_transaction_folio_rel",
        column1="folio_id",
        column2="payment_transaction_id",
    )
    payment_ids = fields.Many2many(
        string="Bank Payments",
        help="Payments",
        readonly=True,
        copy=False,
        comodel_name="account.payment",
        relation="account_payment_folio_rel",
        column1="folio_id",
        column2="payment_id",
    )
    statement_line_ids = fields.Many2many(
        string="Cash Payments",
        help="Statement lines",
        readonly=True,
        copy=False,
        comodel_name="account.bank.statement.line",
        relation="account_bank_statement_folio_rel",
        column1="folio_id",
        column2="account_journal_id",
    )
    payment_term_id = fields.Many2one(
        string="Payment Terms",
        help="Payment terms for current folio.",
        readonly=False,
        store=True,
        index=True,
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
    untaxed_amount_to_invoice = fields.Monetary(
        string="Amount to invoice",
        help="The amount to invoice",
        readonly=True,
        store=True,
        compute="_compute_untaxed_amount_to_invoice",
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
            ("overpayment", "Overpayment"),
            ("nothing_to_pay", "Nothing to pay"),
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
        index=True,
    )
    closure_reason_id = fields.Many2one(
        string="Closure Reason",
        help="The closure reason for a closure room",
        comodel_name="room.closure.reason",
        index=True,
        check_pms_properties=True,
    )
    out_service_description = fields.Text(
        string="Cause of out of service",
        help="Indicates the cause of out of service",
    )
    segmentation_ids = fields.Many2many(
        string="Segmentation",
        help="Segmentation tags to classify folios",
        comodel_name="res.partner.category",
        ondelete="restrict",
        domain="[('is_used_in_checkin', '=', True)]",
    )
    reservation_type = fields.Selection(
        string="Type",
        help="The type of the reservation. "
        "Can be 'Normal', 'Staff' or 'Out of Service'",
        default=lambda *a: "normal",
        selection=[("normal", "Normal"), ("staff", "Staff"), ("out", "Out of Service")],
    )
    date_order = fields.Datetime(
        help="Date on which folio is sold",
        readonly=True,
        required=True,
        index=True,
        default=fields.Datetime.now,
        states={"draft": [("readonly", False)], "sent": [("readonly", False)]},
        copy=False,
    )
    confirmation_date = fields.Datetime(
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
        help="Customer Mobile",
        store=True,
        readonly=False,
        compute="_compute_mobile",
    )
    partner_incongruences = fields.Char(
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
        help="Details of partner credit card",
    )

    pending_amount = fields.Monetary(
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
    payment_multi = fields.Boolean(
        string="Folio paid with payments assigned to other folios",
        help="Technical field for manage payments with multiple folios assigned",
        readonly=True,
        store=True,
        compute="_compute_amount",
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
    invoice_status = fields.Selection(
        help="Invoice Status; it can be: invoiced, to invoice, to confirm, no",
        readonly=True,
        default="no",
        store=True,
        selection=[
            ("invoiced", "Fully Invoiced"),
            ("to_invoice", "To Invoice"),
            ("to_confirm", "To Confirm"),
            ("no", "Nothing to Invoice"),
        ],
        compute="_compute_get_invoice_status",
        compute_sudo=True,
    )
    force_nothing_to_invoice = fields.Boolean(
        string="Force no invoice",
        help="When you set this field, the folio will be considered as "
        "nothin to invoice, even when there may be ordered "
        "quantities pending to invoice.",
        copy=False,
        compute="_compute_force_nothing_to_invoice",
        readonly=False,
        store=True,
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
        help="Margin in days to create a notice if a payment \
                advance has not been recorded",
    )
    sequence = fields.Integer(
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

    possible_existing_customer_ids = fields.One2many(
        string="Possible existing customer",
        compute="_compute_possible_existing_customer_ids",
        comodel_name="res.partner",
        inverse_name="folio_possible_customer_id",
    )
    first_checkin = fields.Date(
        string="First Folio Checkin",
        readonly=False,
        store=True,
        compute="_compute_first_checkin",
    )
    days_to_checkin = fields.Integer(
        help="""Technical field to facilitate
            filtering by dates related to checkin""",
        compute="_compute_days_to_checkin",
        search="_search_days_to_checkin",
    )
    last_checkout = fields.Date(
        string="Last Folio Checkout",
        readonly=False,
        store=True,
        compute="_compute_last_checkout",
    )
    days_to_checkout = fields.Integer(
        help="""Technical field to facilitate
            filtering by dates related to checkout""",
        compute="_compute_days_to_checkout",
        search="_search_days_to_checkout",
    )
    invoice_to_agency = fields.Boolean(
        string="Invoice Agency",
        help="""Indicates if agency invoices partner
            (it only affects those nights/services sold through the agency)""",
        compute="_compute_invoice_to_agengy",
        store=True,
        readonly=False,
    )
    lang = fields.Selection(
        selection=lambda self: self._get_lang_selection_options(),
        string="Language",
        help="Language used for the folio",
        compute="_compute_lang",
        store=True,
        readonly=False,
    )

    @api.model
    def _get_lang_selection_options(self):
        """Gets the available languages for the selection."""
        langs = self.env["res.lang"].search([])
        return [(lang.code, lang.name) for lang in langs]

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
        for folio in self:
            folio_lines_to_invoice = folio.sale_line_ids.filtered(
                lambda r: r.id in list(lines_to_invoice.keys())
            )
            groups_invoice_lines = folio._get_groups_invoice_lines(
                lines_to_invoice=folio_lines_to_invoice,
                partner_invoice_id=partner_invoice_id,
            )
            for group in groups_invoice_lines:
                folio = folio.with_company(folio.company_id)
                down_payments = folio.env["folio.sale.line"]

                # Invoice values.
                invoice_vals = folio._prepare_invoice(
                    partner_invoice_id=group["partner_id"]
                )
                # Invoice line values (keep only necessary sections).
                current_section_vals = None
                invoice_lines_vals = []
                for line in group["lines"]:
                    if line.display_type == "line_section":
                        current_section_vals = line._prepare_invoice_line(
                            sequence=invoice_item_sequence
                            + folio.sale_line_ids.ids.index(line.id)
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
                            invoice_lines_vals.append(current_section_vals)
                            current_section_vals = None
                        prepared_line = line._prepare_invoice_line(
                            sequence=invoice_item_sequence
                            + folio.sale_line_ids.ids.index(line.id),
                            qty=lines_to_invoice[line.id],
                        )
                        invoice_lines_vals.append(prepared_line)

                # If down payments are present in SO, group them under common section
                if down_payments:
                    down_payments_section = folio._prepare_down_payment_section_line(
                        sequence=invoice_item_sequence
                    )
                    invoice_lines_vals.append(down_payments_section)
                    for down_payment in down_payments:
                        # If the down payment is not for the current partner, skip it
                        # it will be managed manually or by the automatic invoice cron
                        if down_payment.default_invoice_to.id != group["partner_id"]:
                            continue
                        invoice_item_sequence += 1
                        invoice_down_payment_vals = down_payment._prepare_invoice_line(
                            sequence=invoice_item_sequence
                            + folio.sale_line_ids.ids.index(down_payment.id)
                        )
                        invoice_lines_vals.append(invoice_down_payment_vals)

                invoice_vals["invoice_line_ids"] = [
                    (0, 0, invoice_line_id) for invoice_line_id in invoice_lines_vals
                ]

                invoice_vals_list.append(invoice_vals)
            invoice_item_sequence += 1000
        return invoice_vals_list

    def _get_groups_invoice_lines(self, lines_to_invoice, partner_invoice_id=False):
        self.ensure_one()
        groups_invoice_lines = []
        if partner_invoice_id:
            groups_invoice_lines.append(
                {
                    "partner_id": partner_invoice_id,
                    "lines": lines_to_invoice,
                }
            )
        else:
            partners = lines_to_invoice.mapped("default_invoice_to")
            for partner in partners:
                groups_invoice_lines.append(
                    {
                        "partner_id": partner.id,
                        "lines": lines_to_invoice.filtered(
                            lambda r, p=partner: r.default_invoice_to == p
                        ),
                    }
                )
            if any(not line.default_invoice_to for line in lines_to_invoice):
                groups_invoice_lines.append(
                    {
                        "partner_id": self.env.ref("pms.various_pms_partner").id,
                        "lines": lines_to_invoice.filtered(
                            lambda r: not r.default_invoice_to
                        ),
                    }
                )
        return groups_invoice_lines

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

    @api.depends("reservation_ids", "reservation_ids.external_reference")
    def _compute_external_reference(self):
        for folio in self:
            folio.external_reference = folio._get_folio_external_reference()

    def _get_folio_external_reference(self):
        self.ensure_one()
        references = list(set(self.reservation_ids.mapped("external_reference")))
        references = list(filter(bool, references))
        if references:
            return ",".join(references)
        else:
            return False

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
        "service_ids.default_invoice_to",
        "service_ids.service_line_ids.price_day_total",
        "service_ids.service_line_ids.discount",
        "service_ids.service_line_ids.cancel_discount",
        "service_ids.service_line_ids.day_qty",
        "service_ids.service_line_ids.tax_ids",
        "reservation_ids.reservation_line_ids",
        "reservation_ids.reservation_line_ids.price",
        "reservation_ids.reservation_line_ids.discount",
        "reservation_ids.reservation_line_ids.cancel_discount",
        "reservation_ids.reservation_line_ids.default_invoice_to",
        "reservation_ids.tax_ids",
        "reservation_ids.state",
    )
    def _compute_sale_line_ids(self):
        for folio in self.filtered(lambda f: isinstance(f.id, int)):
            sale_lines_vals = []
            if folio.reservation_type in ("normal", "staff"):
                sale_lines_vals_to_drop = []
                seq = 0
                for reservation in sorted(
                    folio.reservation_ids.filtered(lambda r: isinstance(r.id, int)),
                    key=lambda r: r.folio_sequence,
                ):
                    seq += reservation.folio_sequence
                    # RESERVATION LINES
                    reservation_sale_lines = []
                    reservation_sale_lines_to_drop = []
                    if reservation.reservation_line_ids:
                        (
                            reservation_sale_lines,
                            reservation_sale_lines_to_drop,
                        ) = self._get_reservation_sale_lines(
                            folio, reservation, sequence=seq
                        )
                    if reservation_sale_lines:
                        sale_lines_vals.extend(reservation_sale_lines)
                    if reservation_sale_lines_to_drop:
                        sale_lines_vals_to_drop.extend(reservation_sale_lines_to_drop)
                    seq += len(reservation_sale_lines)
                    # RESERVATION SERVICES
                    service_sale_lines = []
                    service_sale_lines_to_drop = []
                    if reservation.service_ids:
                        (
                            service_sale_lines,
                            service_sale_lines_to_drop,
                        ) = self._get_service_sale_lines(
                            folio,
                            reservation,
                            sequence=seq,
                        )
                        if service_sale_lines:
                            sale_lines_vals.extend(service_sale_lines)
                        if service_sale_lines_to_drop:
                            sale_lines_vals_to_drop.extend(service_sale_lines_to_drop)
                    seq += len(service_sale_lines)
                # FOLIO SERVICES
                if folio.service_ids.filtered(lambda r: not r.reservation_id):
                    service_sale_lines = False
                    service_sale_lines_to_drop = False
                    (
                        service_sale_lines,
                        service_sale_lines_to_drop,
                    ) = self._get_folio_services_sale_lines(folio, sequence=seq + 1)
                    if service_sale_lines:
                        sale_lines_vals.extend(service_sale_lines)
                    if service_sale_lines_to_drop:
                        sale_lines_vals_to_drop.extend(service_sale_lines_to_drop)
                if sale_lines_vals:
                    folio.sale_line_ids = sale_lines_vals
                if sale_lines_vals_to_drop:
                    self.env["folio.sale.line"].browse(sale_lines_vals_to_drop).unlink()
            if not sale_lines_vals:
                folio.sale_line_ids = False

    @api.depends("pms_property_id")
    def _compute_company_id(self):
        for record in self:
            record.company_id = record.pms_property_id.company_id

    @api.depends(
        "partner_id", "agency_id", "reservation_ids", "reservation_ids.pricelist_id"
    )
    def _compute_pricelist_id(self):
        for folio in self:
            is_new = not folio.pricelist_id or isinstance(folio.id, models.NewId)
            if folio.reservation_type == "out":
                folio.pricelist_id = False
            elif len(folio.reservation_ids.pricelist_id) == 1:
                folio.pricelist_id = folio.reservation_ids.pricelist_id
            elif is_new and folio.agency_id and folio.agency_id.apply_pricelist:
                folio.pricelist_id = folio.agency_id.property_product_pricelist
            elif (
                is_new
                and folio.partner_id
                and folio.partner_id.property_product_pricelist
                and folio.partner_id.property_product_pricelist.is_pms_available
            ):
                folio.pricelist_id = folio.partner_id.property_product_pricelist
            elif not folio.pricelist_id:
                folio.pricelist_id = folio.pms_property_id.default_pricelist_id

    @api.depends(
        "agency_id",
        "reservation_type",
        "partner_name",
        "email",
        "mobile",
    )
    def _compute_partner_id(self):
        for folio in self:
            if folio.reservation_type == "out":
                folio.partner_id = False
            elif folio.agency_id and folio.invoice_to_agency:
                folio.partner_id = folio.agency_id
            elif not folio.partner_id:
                folio.partner_id = False

    @api.depends("pms_property_id")
    def _compute_user_id(self):
        active_user_id = self.env.uid
        for folio in self:
            if not folio.user_id:
                property_users = folio.pms_property_id.member_ids.filtered(
                    lambda u: u.pms_role == "reception"
                ).mapped("user_id")
                if property_users:
                    if active_user_id in property_users.ids:
                        folio.user_id = active_user_id
                    elif property_users:
                        folio.user_id = property_users[0]
                    else:
                        folio.user_id = active_user_id or folio.pms_property_id.user_id

    @api.depends("pms_property_id")
    def _compute_revenue_user_id(self):
        for folio in self:
            revenue_users = folio.pms_property_id.member_ids.filtered(
                lambda u: u.pms_role == "revenue"
            ).mapped("user_id")
            if revenue_users:
                folio.revenue_user_id = revenue_users[0]
            else:
                folio.revenue_user_id = False

    @api.depends("pms_property_id")
    def _compute_administrative_user_id(self):
        for folio in self:
            administrative_users = folio.pms_property_id.member_ids.filtered(
                lambda u: u.pms_role == "administrative"
            ).mapped("user_id")
            if administrative_users:
                folio.administrative_user_id = administrative_users[0]
            else:
                folio.administrative_user_id = False

    @api.depends("pms_property_id")
    def _compute_manager_user_id(self):
        for folio in self:
            manager_users = folio.pms_property_id.member_ids.filtered(
                lambda u: u.pms_role == "manager"
            ).mapped("user_id")
            if manager_users:
                folio.manager_user_id = manager_users[0]
            else:
                folio.manager_user_id = False

    @api.depends(
        "partner_id",
        "reservation_ids",
        "reservation_ids.partner_id",
        "reservation_ids.checkin_partner_ids",
        "reservation_ids.checkin_partner_ids.partner_id",
    )
    def _compute_partner_invoice_ids(self):
        for folio in self:
            if folio.partner_id:
                addr = folio.partner_id.address_get(["invoice"])
                if addr["invoice"] not in folio.partner_invoice_ids.ids:
                    folio.partner_invoice_ids = [(4, addr["invoice"])]
            for reservation in folio.reservation_ids:
                if reservation.partner_id:
                    addr = reservation.partner_id.address_get(["invoice"])
                    if addr["invoice"] not in folio.partner_invoice_ids.ids:
                        folio.partner_invoice_ids = [(4, addr["invoice"])]
                for checkin in reservation.checkin_partner_ids:
                    if checkin.partner_id:
                        addr = checkin.partner_id.address_get(["invoice"])
                        if addr["invoice"] not in folio.partner_invoice_ids.ids:
                            folio.partner_invoice_ids = [(4, addr["invoice"])]
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
            folio.commission = 0
            for reservation in folio.reservation_ids:
                if reservation.commission_amount != 0:
                    folio.commission = folio.commission + reservation.commission_amount

    @api.depends(
        "reservation_ids",
        "reservation_ids.sale_channel_ids",
        "service_ids",
        "service_ids.sale_channel_origin_id",
    )
    def _compute_sale_channel_ids(self):
        for record in self:
            sale_channel_ids = []
            if record.reservation_ids:
                for sale in record.reservation_ids.mapped("sale_channel_ids.id"):
                    sale_channel_ids.append(sale)
            if record.service_ids:
                for sale in record.service_ids.mapped("sale_channel_origin_id.id"):
                    sale_channel_ids.append(sale)
            sale_channel_ids = list(set(sale_channel_ids))
            record.sale_channel_ids = [(6, 0, sale_channel_ids)]

    @api.depends("sale_line_ids.invoice_lines")
    def _compute_get_invoiced(self):
        # The invoice_ids are obtained thanks to the invoice lines of the SO
        # lines, and we also search for possible refunds created directly from
        # existing invoices. This is necessary since such a refund is not
        # directly linked to the SO.
        for order in self:
            invoices = order.sale_line_ids.invoice_lines.move_id.filtered(
                lambda r: r.move_type
                in ("out_invoice", "out_refund", "out_receipt", "in_receipt")
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

    # is_checkin = fields.Boolean()

    # pylint: disable=W8110
    def _compute_access_url(self):
        super()._compute_access_url()
        for folio in self:
            folio.access_url = "/my/folios/%s" % (folio.id)

    @api.depends("state", "sale_line_ids.invoice_status", "force_nothing_to_invoice")
    def _compute_get_invoice_status(self):
        """
        Compute the invoice status of a Folio. Possible statuses:
        - no: if the Folio is in status 'draft', we consider that there is nothing to
          invoice. This is also the default value if the conditions of no
          other status is met.
        - to_invoice: if any SO line is 'to_invoice', the whole SO is 'to_invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        """
        unconfirmed_orders = self.filtered(lambda folio: folio.state in ["draft"])
        unconfirmed_orders.invoice_status = "no"
        zero_orders = self.filtered(lambda folio: folio.amount_total == 0)
        confirmed_orders = self - unconfirmed_orders - zero_orders
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
            if not order.force_nothing_to_invoice and any(
                invoice_status == "to_invoice" for invoice_status in line_invoice_status
            ):
                order.invoice_status = "to_invoice"
            elif any(inv.state == "draft" for inv in order.move_ids):
                order.invoice_status = "to_confirm"
            elif line_invoice_status and any(
                invoice_status == "invoiced" for invoice_status in line_invoice_status
            ):
                order.invoice_status = "invoiced"
            else:
                order.invoice_status = "no"

    @api.depends("untaxed_amount_to_invoice")
    def _compute_force_nothing_to_invoice(self):
        # If the invoice amount and amount total are the same,
        # and the qty to invoice is not 0, we force nothing to invoice
        for order in self:
            if (
                order.untaxed_amount_to_invoice <= 0
                and sum(order.sale_line_ids.mapped("qty_to_invoice")) != 0
            ):
                order.force_nothing_to_invoice = True
            else:
                order.force_nothing_to_invoice = False

    @api.depends("partner_id", "partner_id.name", "agency_id", "reservation_type")
    def _compute_partner_name(self):
        for record in self:
            if record.partner_id and record.partner_id != record.agency_id:
                record.partner_name = record.partner_id.name
            elif record.agency_id and not record.partner_name:
                # if the customer not is the agency but we dont know
                # the customer's name, set the name provisional
                record.partner_name = _("Reservation from ") + record.agency_id.name
            elif not record.partner_name:
                record.partner_name = False

    @api.depends("partner_id", "partner_id.email", "agency_id")
    def _compute_email(self):
        for record in self:
            self._apply_email(record)

    @api.depends("partner_id", "partner_id.mobile", "agency_id")
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
            if folio.reservation_type != "out":
                folio.pending_checkin_data = len(
                    folio.checkin_partner_ids.filtered(lambda c: c.state == "draft")
                )

    @api.depends("pending_checkin_data")
    def _compute_ratio_checkin_data(self):
        self.ratio_checkin_data = 0
        for folio in self.filtered("reservation_ids"):
            if folio.reservation_type != "out":
                folio.ratio_checkin_data = (
                    (
                        sum(folio.reservation_ids.mapped("adults"))
                        - folio.pending_checkin_data
                    )
                    * 100
                    / sum(folio.reservation_ids.mapped("adults"))
                )

    @api.depends("sale_line_ids.untaxed_amount_to_invoice")
    def _compute_untaxed_amount_to_invoice(self):
        for folio in self:
            folio.untaxed_amount_to_invoice = sum(
                folio.sale_line_ids.filtered(lambda r: not r.is_downpayment).mapped(
                    "untaxed_amount_to_invoice"
                )
            )

    # TODO: Add return_ids to depends
    @api.depends(
        "amount_total",
        "currency_id",
        "company_id",
        "reservation_type",
        "state",
        "payment_ids.state",
        "payment_ids.move_id",
        "payment_ids.move_id.line_ids",
        "payment_ids.move_id.line_ids.date",
        "payment_ids.move_id.line_ids.debit",
        "payment_ids.move_id.line_ids.credit",
        "payment_ids.move_id.line_ids.currency_id",
        "payment_ids.move_id.line_ids.amount_currency",
        "move_ids.amount_residual",
    )
    def _compute_amount(self):
        for record in self:
            if record.reservation_type == "out":
                record.amount_total = 0
                vals = {
                    "payment_state": "nothing_to_pay",
                    "pending_amount": 0,
                    "invoices_paid": 0,
                }
                record.update(vals)
            else:
                # first attempt compute amount search payments refs with only one folio
                mls_one_folio = (
                    record.payment_ids.filtered(lambda pay: len(pay.folio_ids) == 1)
                    .mapped("move_id.line_ids")
                    .filtered(
                        lambda x: x.account_id.account_type == "asset_receivable"
                        and x.parent_state == "posted"
                    )
                )
                advance_amount = record._get_advance_amount(mls_one_folio)
                # Compute 'payment_state'.
                vals = record._get_amount_vals(mls_one_folio, advance_amount)
                # If folio its not paid, search payments refs with more than one folio
                folio_ids = record.payment_ids.mapped("folio_ids.id")
                if vals["pending_amount"] > 0 and len(folio_ids) > 1:
                    folios = self.env["pms.folio"].browse(folio_ids)
                    mls_multi_folio = folios.payment_ids.mapped(
                        "move_id.line_ids"
                    ).filtered(
                        lambda x: x.account_id.account_type == "asset_receivable"
                        and x.parent_state == "posted"
                    )
                    if mls_multi_folio:
                        advance_amount = record._get_advance_amount(mls_multi_folio)
                        vals = record._get_amount_vals(
                            mls_multi_folio, advance_amount, folio_ids
                        )

                record.update(vals)

    def _get_advance_amount(self, mls):
        self.ensure_one()
        advance_amount = 0.0
        for line in mls:
            line_currency = line.currency_id or line.company_id.currency_id
            line_amount = line.amount_currency if line.currency_id else line.balance
            line_amount *= -1
            if line_currency != self.currency_id:
                advance_amount += line.currency_id._convert(
                    line_amount,
                    self.currency_id,
                    self.company_id,
                    line.date or fields.Date.today(),
                )
            else:
                advance_amount += line_amount
        return advance_amount

    def _get_amount_vals(self, mls, advance_amount, folio_ids=False):
        self.ensure_one()
        folios = self
        if folio_ids:
            folios = self.env["pms.folio"].browse(folio_ids)
            mls_one_folio = (
                self.payment_ids.filtered(lambda pay: len(pay.folio_ids) == 1)
                .mapped("move_id.line_ids")
                .filtered(
                    lambda x: x.account_id.internal_type == "asset_receivable"
                    and x.parent_state == "posted"
                )
            )
            amount_folio_residual = self.amount_total - self._get_advance_amount(
                mls_one_folio
            )
            amount_total_residual = sum(folios.mapped("amount_total")) - advance_amount
        else:
            amount_folio_residual = amount_total_residual = (
                sum(folios.mapped("amount_total")) - advance_amount
            )
        total = sum(folios.mapped("amount_total"))

        # REVIEW: Must We ignored services in cancelled folios
        # pending amount?
        # for folio in folios:
        #     if folio.state == "cancel":
        #         total = total - sum(folio.service_ids.mapped("price_total"))
        payment_state = "not_paid"
        if (
            mls
            and float_compare(
                amount_total_residual,
                total,
                precision_rounding=self.currency_id.rounding,
            )
            != 0
        ):
            has_due_amount = float_compare(
                amount_total_residual,
                0.0,
                precision_rounding=self.currency_id.rounding,
            )
            if has_due_amount == 0:
                payment_state = "paid"
            elif has_due_amount > 0:
                payment_state = "partial"
            elif has_due_amount < 0:
                payment_state = "overpayment"
        elif total == 0:
            payment_state = "nothing_to_pay"

        vals = {
            "payment_multi": len(folios) > 1,
            "pending_amount": min(amount_total_residual, amount_folio_residual),
            "invoices_paid": advance_amount,
            "payment_state": payment_state,
        }
        return vals

    def _compute_checkin_partner_count(self):
        for record in self:
            if (
                record.reservation_type in ("normal", "staff")
                and record.reservation_ids
            ):
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

    @api.depends("email", "mobile", "partner_name")
    def _compute_possible_existing_customer_ids(self):
        for record in self:
            record.possible_existing_customer_ids = False
            if record.partner_name:
                possible_customer = self._apply_possible_existing_customer_ids(
                    record.email, record.mobile, record.partner_id
                )
                if possible_customer:
                    record.possible_existing_customer_ids = possible_customer

    @api.depends("reservation_ids", "reservation_ids.checkin")
    def _compute_first_checkin(self):
        for record in self:
            checkins = record.reservation_ids.filtered(lambda r: r.checkin).mapped(
                "checkin"
            )
            if checkins:
                record.first_checkin = min(checkins)

    def _compute_days_to_checkin(self):
        for record in self.filtered("first_checkin"):
            record.days_to_checkin = (record.first_checkin - fields.Date.today()).days

    def _search_days_to_checkin(self, operator, value):
        target_date = fields.Date.today() + datetime.timedelta(days=value)
        if operator in ("=", ">=", ">", "<=", "<"):
            return [("first_checkin", operator, target_date)]
        raise UserError(
            _("Unsupported operator %s for searching on date") % (operator,)
        )

    @api.depends("reservation_ids", "reservation_ids.checkout")
    def _compute_last_checkout(self):
        for record in self:
            if record.reservation_ids:
                checkouts = [
                    reservation.checkout
                    for reservation in record.reservation_ids
                    if reservation.checkout
                ]
                record.last_checkout = max(checkouts) if checkouts else False

    def _compute_days_to_checkout(self):
        for record in self:
            if not record.last_checkout:
                record.days_to_checkout = 0
            else:
                record.days_to_checkout = (
                    record.last_checkout - fields.Date.today()
                ).days

    def _search_days_to_checkout(self, operator, value):
        target_date = fields.Date.today() + datetime.timedelta(days=value)
        if operator in ("=", ">=", ">", "<=", "<"):
            return [("last_checkout", operator, target_date)]
        raise UserError(
            _("Unsupported operator %s for searching on date") % (operator,)
        )

    @api.depends("agency_id")
    def _compute_invoice_to_agengy(self):
        for record in self:
            if not record.agency_id or record.agency_id.invoice_to_agency == "never":
                record.invoice_to_agency = False
            elif record.agency_id.invoice_to_agency == "always":
                record.invoice_to_agency = True
            elif not record.invoice_to_agency:
                record.invoice_to_agency = False

    @api.depends("partner_id")
    def _compute_lang(self):
        for record in self.filtered("partner_id"):
            record.lang = record.partner_id.lang

    def _search_invoice_ids(self, operator, value):
        if operator == "in" and value:
            self.env.cr.execute(
                """
                SELECT array_agg(fo.id)
                    FROM pms_folio fo
                    JOIN folio_sale_line fol ON fol.folio_id = fo.id
                    JOIN folio_sale_line_invoice_rel foli_rel
                        ON foli_rel.sale_line_id = fol.id
                    JOIN account_move_line aml ON aml.id = foli_rel.invoice_line_id
                    JOIN account_move am ON am.id = aml.move_id
                WHERE
                    am.move_type in ('out_invoice', 'out_refund', 'in_receipt') AND
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
                ("out_invoice", "out_refund", "in_receipt"),
            ),
            ("sale_line_ids.invoice_lines.move_id", operator, value),
        ]

    @api.constrains("name")
    def _check_required_partner_name(self):
        for record in self:
            if not record.partner_name and record.reservation_type != "out":
                raise models.ValidationError(_("You must assign a customer name"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New") or "name" not in vals:
                if "pms_property_id" not in vals:
                    raise UserError(_("Property is required"))
                pms_property_id = vals.get("pms_property_id")
                pms_property = self.env["pms.property"].browse(pms_property_id)
                vals["name"] = pms_property.folio_sequence_id._next_do()
        records = super().create(vals_list)
        for record in records:
            record.access_token = record._portal_ensure_token()
        return records

    def write(self, vals):
        reservations_to_update = self.env["pms.reservation"]
        services_to_update = self.env["pms.service"]
        if "sale_channel_origin_id" in vals:
            reservations_to_update = self.get_reservations_to_update_channel(vals)
            services_to_update = self.get_services_to_update_channel(vals)

        res = super().write(vals)
        if reservations_to_update:
            reservations_to_update.sale_channel_origin_id = vals[
                "sale_channel_origin_id"
            ]

        if services_to_update:
            services_to_update.sale_channel_origin_id = vals["sale_channel_origin_id"]

        return res

    @api.model
    def _get_languages(self):
        return self.env["res.lang"].get_installed()

    def get_reservations_to_update_channel(self, vals):
        reservations_to_update = self.env["pms.reservation"]
        for record in self:
            for reservation in record.reservation_ids:
                if (
                    reservation.sale_channel_origin_id == self.sale_channel_origin_id
                ) and (
                    vals["sale_channel_origin_id"]
                    != reservation.sale_channel_origin_id.id
                ):
                    reservations_to_update += reservation
        return reservations_to_update

    def get_services_to_update_channel(self, vals):
        services_to_update = self.env["pms.service"]
        for record in self:
            for service in record.service_ids:
                if (
                    not service.reservation_id
                    and (service.sale_channel_origin_id == self.sale_channel_origin_id)
                    and (
                        vals["sale_channel_origin_id"]
                        != service.sale_channel_origin_id.id
                    )
                ):
                    services_to_update += service
        return services_to_update

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
        """Utility method used to add an "View Customer" button in folio views"""
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
            self.reservation_ids.action_confirm()

        return True

    # MAIL FLOWS

    def action_open_confirmation_mail_composer(self):
        self.ensure_one()
        res_id = False
        res_ids = []
        partner_ids = []
        if self.pms_property_id.property_confirmed_template:
            template = self.pms_property_id.property_confirmed_template
        else:
            raise ValidationError(
                _(
                    "You must select a confirmation template "
                    "in the email configuration menu of the property"
                )
            )
        model = "pms.folio"
        partner_ids = [self.partner_id.id]
        res_id = self.id
        composition_mode = "comment"
        ctx = dict(
            model=model,
            default_model=model,
            default_template_id=template and template.id or False,
            default_composition_mode=composition_mode,
            partner_ids=partner_ids,
            force_email=True,
        )
        return self.action_open_mail_composer(ctx, res_id=res_id, res_ids=res_ids)

    def action_open_modification_mail_composer(self):
        self.ensure_one()
        res_id = False
        res_ids = []
        partner_ids = []
        if self.pms_property_id.property_modified_template:
            template = self.pms_property_id.property_modified_template
        else:
            raise ValidationError(
                _(
                    "You must select a modification template "
                    "in the email configuration menu of the property"
                )
            )
        model = "pms.folio"
        partner_ids = [self.partner_id.id]
        res_id = self.id
        composition_mode = "comment"

        ctx = dict(
            model=model,
            default_model=model,
            default_template_id=template and template.id or False,
            default_composition_mode=composition_mode,
            partner_ids=partner_ids,
            force_email=True,
        )
        return self.action_open_mail_composer(ctx, res_id=res_id, res_ids=res_ids)

    def action_open_exit_mail_composer(self):
        self.ensure_one()
        res_id = False
        res_ids = []
        partner_ids = []

        if self.pms_property_id.property_exit_template:
            template = self.pms_property_id.property_exit_template
        else:
            raise ValidationError(
                _(
                    "You must select a exit template in "
                    "the email configuration menu of the property"
                )
            )
        model = "pms.checkin.partner"
        composition_mode = "mass_mail"
        for checkin_partner in self.checkin_partner_ids:
            if checkin_partner.state == "done":
                partner_ids.append(checkin_partner.partner_id.id)
                res_ids.append(checkin_partner.id)
        ctx = dict(
            model=model,
            default_model=model,
            default_template_id=template and template.id or False,
            default_composition_mode=composition_mode,
            partner_ids=partner_ids,
            force_email=True,
        )
        return self.action_open_mail_composer(ctx, res_id=res_id, res_ids=res_ids)

    def action_open_cancelation_mail_composer(self):
        self.ensure_one()
        res_id = False
        res_ids = []
        partner_ids = []
        if self.pms_property_id.property_canceled_template:
            template = self.pms_property_id.property_canceled_template
        else:
            raise ValidationError(
                _(
                    "You must select a cancelation template "
                    "in the email configuration menu of the property"
                )
            )
        model = "pms.reservation"
        composition_mode = "mass_mail"
        for reservation in self.reservation_ids:
            if reservation.state == "cancel":
                partner_ids.append(reservation.partner_id.id)
                res_ids.append(reservation.id)
        ctx = dict(
            model=model,
            default_model=model,
            default_template_id=template and template.id or False,
            default_composition_mode=composition_mode,
            partner_ids=partner_ids,
            force_email=True,
        )
        return self.action_open_mail_composer(ctx, res_id=res_id, res_ids=res_ids)

    def action_open_mail_composer(self, ctx, res_id=False, res_ids=False):
        compose_form = self.env.ref(
            "mail.email_compose_message_wizard_form", raise_if_not_found=False
        )
        composition_mode = ctx.get("default_composition_mode")
        if composition_mode == "comment":
            ctx.update(
                default_res_id=res_id,
                record_id=res_id,
            )
        else:
            ctx.update(
                active_ids=res_ids,
            )
        return {
            "name": _("Send Mail "),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form.id, "form")],
            "view_id": compose_form.id,
            "target": "new",
            "context": ctx,
        }

    def _message_post_after_hook(self, message, msg_vals):
        res = super()._message_post_after_hook(message, msg_vals)
        for folio in self:
            for follower in folio.message_follower_ids:
                follower.sudo().unlink()
        return res

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

    # ruff: noqa: C901
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
            self = self.with_context(lines_auto_add=True)
            lines_to_invoice = dict()
            for line in self.sale_line_ids.filtered(
                lambda r: r.qty_to_invoice > 0
                or (r.qty_to_invoice < 0 and final)
                or r.display_type == "line_note"
            ):
                if not self._context.get("autoinvoice"):
                    lines_to_invoice[line.id] = (
                        0 if line.display_type else line.qty_to_invoice
                    )
                elif (
                    line.autoinvoice_date
                    and line.autoinvoice_date <= fields.Date.today()
                ):
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
            invoice_vals_list = self._get_group_vals_list(invoice_vals_list)

        partner_invoice = self.env["res.partner"].browse(partner_invoice_id)
        partner_invoice_policy = self.pms_property_id.default_invoicing_policy
        if partner_invoice and partner_invoice.invoicing_policy != "property":
            partner_invoice_policy = partner_invoice.invoicing_policy
        invoice_date = False
        if date:
            invoice_date = date
        if partner_invoice_policy == "checkout":
            margin_days_autoinvoice = (
                self.pms_property_id.margin_days_autoinvoice
                if partner_invoice.margin_days_autoinvoice == 0
                else partner_invoice.margin_days_autoinvoice
            )
            invoice_date = max(
                self.env["pms.reservation"]
                .search([("sale_line_ids", "in", lines_to_invoice.keys())])
                .mapped("checkout")
            ) + datetime.timedelta(days=margin_days_autoinvoice)
        if partner_invoice_policy == "month_day":
            month_day = (
                self.pms_property_id.invoicing_month_day
                if partner_invoice.invoicing_month_day == 0
                else partner_invoice.invoicing_month_day
            )
            invoice_date = datetime.date(
                datetime.date.today().year,
                datetime.date.today().month,
                month_day,
            )
            if invoice_date < datetime.date.today():
                invoice_date = datetime.date(
                    datetime.date.today().year,
                    datetime.date.today().month + 1,
                    month_day,
                )
        if invoice_date:
            if (
                self.company_id.period_lock_date
                and invoice_date < self.company_id.period_lock_date
                and not self.user_has_groups("account.group_account_manager")
            ):
                raise UserError(
                    _(
                        "The period to create this invoice is locked. "
                        "Please contact your administrator to unlock it."
                    )
                )
            if invoice_date < datetime.date.today() and not self._context.get(
                "autoinvoice"
            ):
                invoice_date = datetime.date.today()
            key_field = (
                "invoice_date"
                if invoice_date <= fields.Date.today()
                else "invoice_date_due"
            )
            for vals in invoice_vals_list:
                vals["date"] = invoice_date
                vals[key_field] = invoice_date

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
        moves = self._create_account_moves(invoice_vals_list)

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
            move.sudo().message_post_with_view(
                "mail.message_origin_link",
                values={
                    "self": move,
                    "origin": move.line_ids.mapped("folio_line_ids.folio_id"),
                },
                subtype_id=self.env.ref("mail.mt_note").id,
            )
        return moves

    def _create_account_moves(self, invoice_vals_list):
        moves = self.env["account.move"]
        for invoice_vals in invoice_vals_list:
            if invoice_vals["move_type"] == "out_invoice":
                move = (
                    self.env["account.move"]
                    .sudo()
                    .with_context(default_move_type="out_invoice")
                    .create(invoice_vals)
                )
            moves += move
        return moves

    def _get_group_vals_list(self, invoice_vals_list):
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
        return new_invoice_vals_list

    def _prepare_invoice(self, partner_invoice_id=False):
        """
        Prepare the dict of values to create the new invoice for a folio.
        This method may be overridden to implement custom invoice generation
        (making sure to call super() to establish a clean extension chain).
        """
        self.ensure_one()
        journal = self.pms_property_id._get_folio_default_journal(
            partner_invoice_id=partner_invoice_id,
            room_ids=self.reservation_ids.mapped("reservation_line_ids.room_id.id"),
        )
        if not journal:
            journal = (
                self.env["account.move"]
                .with_context(
                    default_move_type="out_invoice",
                    default_company_id=self.company_id.id,
                    default_pms_property_id=self.pms_property_id.id,
                )
                ._search_default_journal()
            )
        if not journal:
            raise UserError(
                _(
                    "Please define an accounting sales journal"
                    " for the company {company_name} ({company_id})."
                ).format(
                    company_name=self.company_id.name,
                    company_id=self.company_id.id,
                )
            )
        ref = ""
        if self.name:
            ref = self.name
        if self.external_reference:
            ref += " - " + self.external_reference
        invoice_vals = {
            "name": "/",
            "ref": ref,
            "move_type": "out_invoice",
            "narration": self.note,
            "currency_id": self.pricelist_id.currency_id.id,
            # 'campaign_id': self.campaign_id.id,
            # 'medium_id': self.medium_id.id,
            # 'source_id': self.source_id.id,
            "invoice_user_id": self.user_id and self.user_id.id,
            "partner_id": partner_invoice_id,
            "journal_id": journal.id,  # company comes from the journal
            "invoice_origin": self.name,
            "invoice_payment_term_id": self.payment_term_id.id,
            "transaction_ids": [(6, 0, self.transaction_ids.ids)],
            "invoice_line_ids": [],
            "company_id": self.company_id.id,
            "payment_reference": self.name,
            "fiscal_position_id": self.env["account.fiscal.position"]
            .with_company(self.company_id.id)
            ._get_fiscal_position(self.env["res.partner"].browse(partner_invoice_id))
            .id,
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
        pay_type=False,
        ref=False,
    ):
        """
        create folio payment
        type: set cash to use statement or bank to use account.payment,
        by default, use the journal type
        """
        if not pay_type:
            pay_type = journal.type

        reference = folio.name
        if folio.external_reference:
            reference += " - " + folio.external_reference
        if ref and ref not in reference:
            reference += ": " + ref
        vals = {
            "journal_id": journal.id,
            "partner_id": partner.id if partner else False,
            "amount": amount,
            "date": date or fields.Date.today(),
            "ref": reference,
            "folio_ids": [(6, 0, [folio.id])],
            "payment_type": "inbound",
            "partner_type": "customer",
            "state": "draft",
            "origin_reference": folio.external_reference,
        }
        pay = self.env["account.payment"].create(vals)
        pay.sudo().message_post_with_view(
            "mail.message_origin_link",
            values={
                "self": pay,
                "origin": folio,
            },
            subtype_id=self.env.ref("mail.mt_note").id,
            email_from=user.partner_id.email_formatted
            or folio.pms_property_id.email_formatted,
        )

        pay.action_post()

        # Review: force to autoreconcile payment with invoices already created
        pay.flush_recordset()
        for move in folio.move_ids:
            move.sudo()._autoreconcile_folio_payments()

        folio.sudo().message_post(
            body=_("Payment: <b>%(amount)s</b> by <b>%(journal)s</b>")
            % {"amount": amount, "journal": journal.display_name},
            email_from=user.partner_id.email_formatted
            or folio.pms_property_id.email_formatted,
        )
        for reservation in folio.reservation_ids:
            reservation.sudo().message_post(
                body=_("Payment: <b>%(amount)s</b> by <b>%(journal)s</b>")
                % {"amount": amount, "journal": journal.display_name},
                email_from=user.partner_id.email_formatted
                or folio.pms_property_id.email_formatted,
            )
        return True

    def do_refund(
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
        pay_type=False,
        ref=False,
    ):
        """
        create folio refund
        type: set cash to use statement or bank to use account.payment,
        by default, use the journal type
        """
        if not pay_type:
            pay_type = journal.type
        reference = folio.name
        if folio.external_reference:
            reference += " - " + folio.external_reference
        if ref and ref not in reference:
            reference += ": " + ref
        vals = {
            "journal_id": journal.id,
            "partner_id": partner.id if partner else False,
            "amount": amount if amount > 0 else -amount,
            "date": date or fields.Date.today(),
            "ref": reference,
            "folio_ids": [(6, 0, [folio.id])],
            "payment_type": "outbound",
            "partner_type": "customer",
            "state": "draft",
        }
        pay = self.env["account.payment"].create(vals)
        pay.sudo().message_post_with_view(
            "mail.message_origin_link",
            values={
                "self": pay,
                "origin": folio,
            },
            subtype_id=self.env.ref("mail.mt_note").id,
            email_from=user.partner_id.email_formatted
            or folio.pms_property_id.email_formatted,
        )
        pay.action_post()

        folio.sudo().message_post(
            body=_("Refund: <b>%(amount)s</b> by <b>%(journal)s</b>")
            % {"amount": amount, "journal": journal.display_name},
            email_from=user.partner_id.email_formatted
            or folio.pms_property_id.email_formatted,
        )
        for reservation in folio.reservation_ids:
            reservation.sudo().message_post(
                body=_("Refund: <b>%(amount)s</b> by <b>%(journal)s</b>")
                % {"amount": amount, "journal": journal.display_name},
                email_from=user.partner_id.email_formatted
                or folio.pms_property_id.email_formatted,
            )
        return True

    def open_wizard_several_partners(self):
        ctx = dict(
            folio_id=self.id,
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
    def _get_reservation_sale_lines(self, folio, reservation, sequence):
        sale_reservation_vals = []
        if not reservation.sale_line_ids.filtered(lambda x: x.name == reservation.name):
            sale_reservation_vals.append(
                (
                    0,
                    0,
                    {
                        "name": reservation.name,
                        "display_type": "line_section",
                        "product_id": False,
                        "product_uom_qty": 0,
                        "discount": 0,
                        "price_unit": 0,
                        "tax_ids": False,
                        "folio_id": folio.id,
                        "reservation_id": reservation.id,
                        "sequence": sequence,
                    },
                )
            )
            note_vals = self._get_reservation_note_vals(reservation, sequence)
            if note_vals:
                sale_reservation_vals.append(note_vals)
        else:
            sequence += 1
            sale_reservation_vals.append(
                (
                    1,
                    reservation.sale_line_ids.filtered(
                        lambda x: x.name == reservation.name
                    ).id,
                    {
                        "sequence": sequence,
                    },
                )
            )
            # delete old auto reservation note
            old_note = reservation.sale_line_ids.filtered(
                lambda x: x.auto_reservation_note
            )
            if old_note:
                sale_reservation_vals.append((2, old_note.id))
            note_vals = self._get_reservation_note_vals(reservation, sequence)
            if note_vals:
                sale_reservation_vals.append(note_vals)
        expected_reservation_lines = self.env["pms.reservation.line"].read_group(
            [
                ("reservation_id", "=", reservation.id),
                ("cancel_discount", "<", 100),
            ],
            ["price", "discount", "cancel_discount", "default_invoice_to"],
            ["price", "discount", "cancel_discount", "default_invoice_to"],
            lazy=False,
        )
        current_sale_line_ids = reservation.sale_line_ids.filtered(
            lambda x: x.reservation_id.id == reservation.id
            and not x.display_type
            and not x.service_id
        )

        for index, item in enumerate(expected_reservation_lines):
            sequence += 1
            lines_to = self.env["pms.reservation.line"].search(item["__domain"])
            final_discount = self.concat_discounts(
                item["discount"], item["cancel_discount"]
            )
            partner_invoice = lines_to.mapped("default_invoice_to")
            if current_sale_line_ids and index <= (len(current_sale_line_ids) - 1):
                current = {
                    "price_unit": item["price"],
                    "discount": final_discount,
                    "reservation_line_ids": [(6, 0, lines_to.ids)],
                    "sequence": sequence,
                    "default_invoice_to": (
                        partner_invoice[0].id
                        if partner_invoice
                        else current_sale_line_ids[index].default_invoice_to
                    ),
                }
                sale_reservation_vals.append(
                    (1, current_sale_line_ids[index].id, current)
                )
            else:
                new = {
                    "reservation_id": reservation.id,
                    "price_unit": item["price"],
                    "discount": final_discount,
                    "folio_id": folio.id,
                    "product_id": reservation.room_type_id.product_id.id,
                    "tax_ids": [(6, 0, reservation.tax_ids.ids)],
                    "reservation_line_ids": [(6, 0, lines_to.ids)],
                    "sequence": sequence,
                    "default_invoice_to": (
                        partner_invoice[0].id if partner_invoice else False
                    ),
                }
                sale_reservation_vals.append((0, 0, new))
        folio_sale_lines_to_remove = []
        if len(expected_reservation_lines) < len(current_sale_line_ids):
            folio_sale_lines_to_remove = [
                value.id
                for index, value in enumerate(current_sale_line_ids)
                if index > (len(expected_reservation_lines) - 1)
            ]
        return sale_reservation_vals, folio_sale_lines_to_remove

    def _get_reservation_note_vals(self, reservation, sequence):
        try:
            note = self.get_reservation_notes(reservation)
            if note:
                sequence += 1
                return (
                    0,
                    0,
                    {
                        "name": note,
                        "display_type": "line_note",
                        "product_id": False,
                        "product_uom_qty": 0,
                        "discount": 0,
                        "price_unit": 0,
                        "tax_ids": False,
                        "folio_id": reservation.folio_id.id,
                        "reservation_id": reservation.id,
                        "auto_reservation_note": True,
                        "sequence": sequence,
                    },
                )
            else:
                return False
        except Exception as e:
            _logger.error(
                "Error while getting reservation notes for folio %s: %s",
                reservation.folio_id.id,
                e,
            )

    @api.model
    def _get_service_sale_lines(self, folio, reservation, sequence):
        sale_service_vals = []
        folio_sale_lines_to_remove = []
        for service in reservation.service_ids:
            expected_reservation_services = self.env["pms.service.line"].read_group(
                [
                    ("reservation_id", "=", reservation.id),
                    ("service_id", "=", service.id),
                    ("cancel_discount", "<", 100),
                ],
                ["price_unit", "discount", "cancel_discount", "default_invoice_to"],
                ["price_unit", "discount", "cancel_discount", "default_invoice_to"],
                lazy=False,
            )
            current_sale_service_ids = reservation.sale_line_ids.filtered(
                lambda x, s=service: x.reservation_id.id == reservation.id
                and not x.display_type
                and x.service_id.id == s.id
            )

            for index, item in enumerate(expected_reservation_services):
                lines_to = self.env["pms.service.line"].search(item["__domain"])
                final_discount = self.concat_discounts(
                    item["discount"], item["cancel_discount"]
                )
                partner_invoice = lines_to.mapped("default_invoice_to")
                if current_sale_service_ids and index <= (
                    len(current_sale_service_ids) - 1
                ):
                    current = {
                        "price_unit": item["price_unit"],
                        "discount": final_discount,
                        "service_line_ids": [(6, 0, lines_to.ids)],
                        "sequence": sequence,
                        "default_invoice_to": (
                            partner_invoice[0].id
                            if partner_invoice
                            else current_sale_service_ids[index].default_invoice_to
                        ),
                    }
                    sale_service_vals.append(
                        (1, current_sale_service_ids[index].id, current)
                    )
                else:
                    new = {
                        "service_id": service.id,
                        "price_unit": item["price_unit"],
                        "discount": final_discount,
                        "folio_id": folio.id,
                        "reservation_id": reservation.id,
                        "service_line_ids": [(6, 0, lines_to.ids)],
                        "product_id": service.product_id.id,
                        "tax_ids": [(6, 0, service.tax_ids.ids)],
                        "sequence": sequence,
                        "default_invoice_to": (
                            partner_invoice[0].id if partner_invoice else False
                        ),
                    }
                    sale_service_vals.append((0, 0, new))
                sequence = sequence + 1
            if len(expected_reservation_services) < len(current_sale_service_ids):
                folio_sale_lines_to_remove = [
                    value.id
                    for index, value in enumerate(current_sale_service_ids)
                    if index > (len(expected_reservation_services) - 1)
                ]
        return sale_service_vals, folio_sale_lines_to_remove

    @api.model
    def _get_folio_services_sale_lines(self, folio, sequence):
        folio_services = folio.service_ids.filtered(lambda x: not x.reservation_id)
        sale_folio_lines = []
        sale_folio_lines_to_remove = []
        if folio_services:
            if not folio.sale_line_ids.filtered(lambda x: x.name == _("Others")):
                folio.sale_line_ids = [
                    (
                        0,
                        False,
                        {
                            "display_type": "line_section",
                            "product_id": False,
                            "product_uom_qty": 0,
                            "discount": 0,
                            "price_unit": 0,
                            "tax_ids": False,
                            "name": _("Others"),
                            "sequence": sequence,
                        },
                    )
                ]
            for folio_service in folio_services:
                sequence += 1
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
                    lambda x, fs=folio_service: x.service_id.folio_id.id == folio.id
                    and not x.display_type
                    and not x.reservation_id
                    and x.service_id.id == fs.id
                )

                for index, item in enumerate(expected_folio_services):
                    lines_to = self.env["pms.service.line"].search(item["__domain"])
                    final_discount = self.concat_discounts(
                        item["discount"], item["cancel_discount"]
                    )
                    if current_folio_service_ids and index <= (
                        len(current_folio_service_ids) - 1
                    ):
                        current = {
                            "price_unit": item["price_unit"],
                            "discount": final_discount,
                            "service_line_ids": [(6, 0, lines_to.ids)],
                            "sequence": sequence,
                        }
                        sale_folio_lines.append(
                            (1, current_folio_service_ids[index].id, current)
                        )
                    else:
                        new = {
                            "service_id": folio_service.id,
                            "price_unit": item["price_unit"],
                            "discount": final_discount,
                            "folio_id": folio.id,
                            "service_line_ids": [(6, 0, lines_to.ids)],
                            "product_id": folio_service.product_id.id,
                            "tax_ids": [(6, 0, folio_service.tax_ids.ids)],
                            "sequence": sequence,
                        }
                        sale_folio_lines.append((0, 0, new))
                if len(expected_folio_services) < len(current_folio_service_ids):
                    sale_folio_lines_to_remove = [
                        value.id
                        for index, value in enumerate(current_folio_service_ids)
                        if index > (len(expected_folio_services) - 1)
                    ]
        else:
            sale_folio_lines_to_remove = folio.sale_line_ids.filtered(
                lambda x: x.name == _("Others")
            )
        return sale_folio_lines, sale_folio_lines_to_remove

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
    def concat_discounts(self, discount, cancel_discount):
        discount_factor = 1.0
        for discount_item in [discount, cancel_discount]:
            discount_factor = discount_factor * ((100.0 - discount_item) / 100.0)
        final_discount = 100.0 - (discount_factor * 100.0)
        return final_discount

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

    @api.model
    def _apply_possible_existing_customer_ids(
        self, email=False, mobile=False, partner=False
    ):
        possible_customer = False
        if email and not partner:
            possible_customer = self.env["res.partner"].search([("email", "=", email)])
        if mobile and not partner:
            possible_customer = self.env["res.partner"].search(
                [("mobile", "=", mobile)]
            )
        return possible_customer

    def _create_payment_transaction(self, vals):
        # Ensure the currencies are the same.
        currency = self[0].currency_id
        if any(folio.currency_id != currency for folio in self):
            raise ValidationError(
                _(
                    "A transaction can't be linked to folios"
                    " having different currencies."
                )
            )

        # Ensure the partner are the same.
        partner = self[0].partner_id
        if any(folio.partner_id != partner for folio in self):
            raise ValidationError(
                _("A transaction can't be linked to folios having different partners.")
            )

        # Try to retrieve the acquirer. However, fallback to the token's acquirer.
        acquirer_id = vals.get("acquirer_id")
        acquirer = None
        payment_token_id = vals.get("payment_token_id")

        if payment_token_id:
            payment_token = self.env["payment.token"].sudo().browse(payment_token_id)

            # Check payment_token/acquirer matching or take the acquirer from token
            if acquirer_id:
                acquirer = self.env["payment.provider"].browse(acquirer_id)
                if payment_token and payment_token.acquirer_id != acquirer:
                    raise ValidationError(
                        _(
                            "Invalid token found! Token"
                            "acquirer %(token_acquirer)s != %(acquirer)s"
                        )
                        % {
                            "token_acquirer": payment_token.acquirer_id.name,
                            "acquirer": acquirer.name,
                        }
                    )
                if payment_token and payment_token.partner_id != partner:
                    raise ValidationError(
                        _(
                            "Invalid token found! Token"
                            "partner %(token_partner)s != %(partner)s"
                        )
                        % {
                            "token_partner": payment_token.partner.name,
                            "partner": partner.name,
                        }
                    )
            else:
                acquirer = payment_token.acquirer_id

        # Check an acquirer is there.
        if not acquirer_id and not acquirer:
            raise ValidationError(
                _("A payment acquirer is required to create a transaction.")
            )

        if not acquirer:
            acquirer = self.env["payment.provider"].browse(acquirer_id)

        # Check a journal is set on acquirer.
        if not acquirer.journal_id:
            raise ValidationError(
                _("A journal must be specified for the acquirer %s.", acquirer.name)
            )

        if not acquirer_id and acquirer:
            vals["acquirer_id"] = acquirer.id

        vals.update(
            {
                "amount": sum(self.mapped("amount_total")),
                "currency_id": currency.id,
                "partner_id": partner.id,
                "folio_ids": [(6, 0, self.ids)],
            }
        )
        transaction = self.env["payment.transaction"].create(vals)

        # Process directly if payment_token
        if transaction.payment_token_id:
            transaction.s2s_do_transaction()

        return transaction

    def _get_default_payment_link_values(self):
        self.ensure_one()
        return {
            "description": self.name[-8:],
            "amount": self.pending_amount,
            "currency_id": self.currency_id.id,
            "partner_id": (
                self.partner_id.id
                if self.partner_id
                else self.env.ref("pms.various_pms_partner").id
            ),
            "amount_max": self.pending_amount,
        }

    def get_reservation_notes(self, reservation):
        """
        Add folio line note with reservation content
        """
        if reservation.pms_property_id.invoice_reservation_note_template:
            return reservation._render_invoice_note()

    def _get_portal_return_action(self):
        """Return the action used to display orders
        when returning from customer portal."""
        self.ensure_one()
        return self.env.ref("pms.open_pms_folio1_form_tree_all")
