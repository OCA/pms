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

    # Default Methods ang Gets
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

    # Fields declaration
    name = fields.Char(
        string="Folio Number", readonly=True, index=True, default=lambda self: _("New")
    )
    pms_property_id = fields.Many2one(
        "pms.property",
        default=lambda self: self.env.user.get_active_property_ids()[0],
        required=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        compute="_compute_partner_id",
        tracking=True,
        ondelete="restrict",
        store=True,
        readonly=False,
    )
    reservation_ids = fields.One2many(
        "pms.reservation",
        "folio_id",
        readonly=False,
        states={"done": [("readonly", True)]},
        help="Room reservation detail.",
    )
    number_of_rooms = fields.Integer(
        "Number of Rooms",
        compute="_compute_number_of_rooms",
        store="True",
    )
    service_ids = fields.One2many(
        "pms.service",
        "folio_id",
        readonly=False,
        states={"done": [("readonly", True)]},
        help="Services detail provide to customer and it will "
        "include in main Invoice.",
    )
    sale_line_ids = fields.One2many(
        "folio.sale.line",
        "folio_id",
        compute="_compute_sale_line_ids",
        compute_sudo=True,
        store="True",
    )
    invoice_count = fields.Integer(
        string="Invoice Count", compute="_compute_get_invoiced", readonly=True
    )
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        default=lambda self: self.env.company,
    )
    move_line_ids = fields.Many2many(
        "account.move.line",
        "payment_folio_rel",
        "folio_id",
        "move_id",
        string="Payments",
        readonly=True,
    )
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        "Analytic Account",
        readonly=True,
        states={"draft": [("readonly", False)], "sent": [("readonly", False)]},
        help="The analytic account related to a folio.",
        copy=False,
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="pricelist_id.currency_id",
        string="Currency",
        readonly=True,
        required=True,
        ondelete="restrict",
    )
    pricelist_id = fields.Many2one(
        "product.pricelist",
        string="Pricelist",
        ondelete="restrict",
        compute="_compute_pricelist_id",
        store=True,
        readonly=False,
        help="Pricelist for current folio.",
    )
    commission = fields.Float(
        string="Commission",
        compute="_compute_commission",
        store=True,
        readonly=True,
        default=0,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Salesperson",
        index=True,
        ondelete="restrict",
        tracking=True,
        compute="_compute_user_id",
        store=True,
        readonly=False,
    )
    agency_id = fields.Many2one(
        "res.partner",
        string="Agency",
        ondelete="restrict",
        domain=[("is_agency", "=", True)],
    )
    channel_type_id = fields.Many2one(
        "pms.sale.channel",
        compute="_compute_channel_type_id",
        readonly=False,
        store=True,
        string="Direct Sale Channel",
        ondelete="restrict",
        domain=[("channel_type", "=", "direct")],
    )
    transaction_ids = fields.Many2many(
        "payment.transaction",
        "folio_transaction_rel",
        "folio_id",
        "transaction_id",
        string="Transactions",
        copy=False,
        readonly=True,
    )
    payment_term_id = fields.Many2one(
        "account.payment.term",
        string="Payment Terms",
        ondelete="restrict",
        compute="_compute_payment_term_id",
        store=True,
        readonly=False,
        help="Pricelist for current folio.",
    )
    checkin_partner_ids = fields.One2many("pms.checkin.partner", "folio_id")
    count_rooms_pending_arrival = fields.Integer(
        "Pending Arrival",
        compute="_compute_count_rooms_pending_arrival",
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
    move_ids = fields.Many2many(
        "account.move",
        string="Invoices",
        compute="_compute_get_invoiced",
        search="_search_invoice_ids",
        readonly=True,
        copy=False,
    )
    payment_state = fields.Selection(
        selection=[
            ("not_paid", "Not Paid"),
            ("paid", "Paid"),
            ("partial", "Partially Paid"),
        ],
        string="Payment Status",
        store=True,
        readonly=True,
        copy=False,
        tracking=True,
        compute="_compute_amount",
    )
    partner_invoice_id = fields.Many2one(
        "res.partner",
        string="Invoice Address",
        compute="_compute_partner_invoice_id",
        store=True,
        readonly=False,
        help="Invoice address for current group.",
    )
    partner_invoice_state_id = fields.Many2one(related="partner_invoice_id.state_id")
    partner_invoice_country_id = fields.Many2one(
        related="partner_invoice_id.country_id"
    )
    fiscal_position_id = fields.Many2one(
        "account.fiscal.position", string="Fiscal Position"
    )
    closure_reason_id = fields.Many2one("room.closure.reason")
    segmentation_ids = fields.Many2many(
        "res.partner.category", string="Segmentation", ondelete="restrict"
    )
    client_order_ref = fields.Char(string="Customer Reference", copy=False)
    reservation_type = fields.Selection(
        [("normal", "Normal"), ("staff", "Staff"), ("out", "Out of Service")],
        string="Type",
        default=lambda *a: "normal",
    )
    date_order = fields.Datetime(
        string="Order Date",
        required=True,
        readonly=True,
        index=True,
        states={"draft": [("readonly", False)], "sent": [("readonly", False)]},
        copy=False,
        default=fields.Datetime.now,
    )
    confirmation_date = fields.Datetime(
        string="Confirmation Date",
        readonly=True,
        index=True,
        help="Date on which the folio is confirmed.",
        copy=False,
    )
    state = fields.Selection(
        [
            ("draft", "Quotation"),
            ("sent", "Quotation Sent"),
            ("confirm", "Confirmed"),
            ("done", "Locked"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        readonly=True,
        copy=False,
        index=True,
        tracking=True,
        default="draft",
    )
    # Partner fields for being used directly in the Folio views---------
    email = fields.Char("E-mail", related="partner_id.email")
    mobile = fields.Char("Mobile", related="partner_id.mobile")
    phone = fields.Char("Phone", related="partner_id.phone")
    partner_internal_comment = fields.Text(
        string="Internal Partner Notes", related="partner_id.comment"
    )
    # Payment Fields-----------------------------------------------------
    credit_card_details = fields.Text("Credit Card Details")

    # Amount Fields------------------------------------------------------
    pending_amount = fields.Monetary(
        compute="_compute_amount", store=True, string="Pending in Folio"
    )
    # refund_amount = fields.Monetary(
    #     compute="_compute_amount", store=True, string="Payment Returns"
    # )
    invoices_paid = fields.Monetary(
        compute="_compute_amount",
        store=True,
        tracking=True,
        string="Payments",
    )
    amount_untaxed = fields.Monetary(
        string="Untaxed Amount",
        store=True,
        readonly=True,
        compute="_compute_amount_all",
        tracking=True,
    )
    amount_tax = fields.Monetary(
        string="Taxes", store=True, readonly=True, compute="_compute_amount_all"
    )
    amount_total = fields.Monetary(
        string="Total",
        store=True,
        readonly=True,
        compute="_compute_amount_all",
        tracking=True,
    )
    # Checkin Fields-----------------------------------------------------
    reservation_pending_arrival_ids = fields.One2many(
        comodel_name="pms.checkin.partner",
        string="Pending Arrival Rooms",
        compute="_compute_reservations_pending_arrival",
    )
    reservations_pending_count = fields.Integer(
        compute="_compute_reservations_pending_arrival"
    )
    max_reservation_prior = fields.Integer(
        string="Max reservation priority on the entire folio",
        compute="_compute_max_reservation_prior",
    )
    # Invoice Fields-----------------------------------------------------
    invoice_status = fields.Selection(
        [
            ("invoiced", "Fully Invoiced"),
            ("to invoice", "To Invoice"),
            ("no", "Nothing to Invoice"),
        ],
        string="Invoice Status",
        compute="_compute_get_invoice_status",
        store=True,
        readonly=True,
        default="no",
        compute_sudo=True,
    )
    # Generic Fields-----------------------------------------------------
    internal_comment = fields.Text(string="Internal Folio Notes")
    cancelled_reason = fields.Text("Cause of cancelled")
    prepaid_warning_days = fields.Integer(
        "Prepaid Warning Days",
        help="Margin in days to create a notice if a payment \
                advance has not been recorded",
    )
    sequence = fields.Integer(string="Sequence", default=10)
    note = fields.Text("Terms and conditions", default=_default_note)
    reference = fields.Char(
        string="Payment Ref.",
        copy=False,
        help="The payment communication of this sale order.",
    )

    # Compute and Search methods
    @api.depends("reservation_ids", "reservation_ids.state")
    def _compute_number_of_rooms(self):
        for folio in self:
            folio.number_of_rooms = len(
                folio.reservation_ids.filtered(lambda a: a.state != "cancelled")
            )

    @api.depends(
        "reservation_ids",
        "service_ids",
        "service_ids.reservation_id",
        "reservation_ids.reservation_line_ids",
        "reservation_ids.reservation_line_ids.price",
        "reservation_ids.reservation_line_ids.discount",
        "reservation_ids.reservation_line_ids.cancel_discount",
    )
    def _compute_sale_line_ids(self):
        for folio in self:
            sale_lines = [(5, 0, 0)]
            reservations = folio.reservation_ids
            services_without_room = folio.service_ids.filtered(
                lambda s: not s.reservation_id
            )
            # TODO: Not delete old sale line ids
            for reservation in reservations:
                sale_lines.append(
                    (
                        0,
                        False,
                        {
                            "display_type": "line_section",
                            "name": reservation.name,
                        },
                    )
                )
                group_lines = {}
                for line in reservation.reservation_line_ids:
                    # On resevations the price, and discounts fields are used
                    # by group, we need pass this in the create line
                    group_key = (
                        reservation.id,
                        line.price,
                        line.discount,
                        line.cancel_discount,
                    )
                    if line.cancel_discount == 100:
                        continue
                    discount_factor = 1.0
                    for discount in [line.discount, line.cancel_discount]:
                        discount_factor = discount_factor * ((100.0 - discount) / 100.0)
                    final_discount = 100.0 - (discount_factor * 100.0)
                    if group_key not in group_lines:
                        group_lines[group_key] = {
                            "reservation_id": reservation.id,
                            "discount": final_discount,
                            "price_unit": line.price,
                            "reservation_line_ids": [(4, line.id)],
                        }
                    else:
                        group_lines[group_key][("reservation_line_ids")].append(
                            (4, line.id)
                        )
                for item in group_lines.items():
                    sale_lines.append((0, False, item[1]))
                for service in reservation.service_ids:
                    # On service the price, and discounts fields are
                    # compute in the sale.order.line
                    sale_lines.append(
                        (
                            0,
                            False,
                            {
                                "name": service.name,
                                "service_id": service.id,
                            },
                        )
                    )
            if services_without_room:
                sale_lines.append(
                    (
                        0,
                        False,
                        {
                            "display_type": "line_section",
                            "name": _("Others"),
                        },
                    )
                )
                for service in services_without_room:
                    sale_lines.append(
                        (
                            0,
                            False,
                            {
                                "name": service.name,
                                "service_id": service.id,
                            },
                        )
                    )
            folio.sale_line_ids = sale_lines

    @api.depends("partner_id", "agency_id")
    def _compute_pricelist_id(self):
        for folio in self:
            if folio.partner_id and folio.partner_id.property_product_pricelist:
                pricelist_id = folio.partner_id.property_product_pricelist.id
            else:
                pricelist_id = self.env.user.pms_property_id.default_pricelist_id.id
            if folio.pricelist_id.id != pricelist_id:
                # TODO: Warning change de pricelist?
                folio.pricelist_id = pricelist_id
            if folio.agency_id and folio.agency_id.apply_pricelist:
                pricelist_id = folio.agency_id.property_product_pricelist.id

    @api.depends("agency_id")
    def _compute_partner_id(self):
        for folio in self:
            if folio.agency_id and folio.agency_id.invoice_agency:
                folio.partner_id = folio.agency_id.id
            elif not folio.partner_id:
                folio.partner_id = False

    @api.depends("partner_id")
    def _compute_user_id(self):
        for folio in self:
            folio.user_id = (folio.partner_id.user_id.id or self.env.uid,)

    @api.depends("partner_id")
    def _compute_partner_invoice_id(self):
        self.partner_invoice_id = False
        for folio in self:
            addr = folio.partner_id.address_get(["invoice"])
            folio.partner_invoice_id = addr["invoice"]

    @api.depends("partner_id")
    def _compute_payment_term_id(self):
        self.payment_term_id = False
        for folio in self:
            folio.payment_term_id = (
                folio.partner_id.property_payment_term_id
                and folio.partner_id.property_payment_term_id.id
                or False
            )

    @api.depends("reservation_ids")
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

    @api.depends("state", "sale_line_ids.invoice_status")
    def _compute_get_invoice_status(self):
        """
        Compute the invoice status of a Folio. Possible statuses:
        - no: if the Folio is in status 'draft', we consider that there is nothing to
          invoice. This is also the default value if the conditions of no
          other status is met.
        - to invoice: if any SO line is 'to invoice', the whole SO is 'to invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        - upselling: if all SO lines are invoiced or upselling, the status is upselling.
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
                invoice_status == "to invoice" for invoice_status in line_invoice_status
            ):
                order.invoice_status = "to invoice"
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

    @api.depends("reservation_ids.price_total", "service_ids.price_total")
    def _compute_amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for record in self.filtered("pricelist_id"):
            amount_untaxed = amount_tax = 0.0
            amount_untaxed = sum(record.reservation_ids.mapped("price_subtotal")) + sum(
                record.service_ids.mapped("price_subtotal")
            )
            amount_tax = sum(record.reservation_ids.mapped("price_tax")) + sum(
                record.service_ids.mapped("price_tax")
            )
            record.update(
                {
                    "amount_untaxed": record.pricelist_id.currency_id.round(
                        amount_untaxed
                    ),
                    "amount_tax": record.pricelist_id.currency_id.round(amount_tax),
                    "amount_total": amount_untaxed + amount_tax,
                }
            )

    @api.depends("reservation_ids", "reservation_ids.state")
    def _compute_count_rooms_pending_arrival(self):
        self.count_rooms_pending_arrival = 0
        for folio in self.filtered("reservation_ids"):
            folio.count_rooms_pending_arrival = len(
                folio.reservation_ids.filtered(
                    lambda c: c.state in ("draf", "confirm", "no_show")
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
                if record.state == "cancelled":
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

    def _compute_max_reservation_prior(self):
        for record in self:
            reservation_priors = record.reservation_ids.mapped("priority")
            record.max_reservation_prior = max(reservation_priors)

    # Action methods

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
            lambda c: c.state in ("draf", "confirm", "no_show")
        )
        action = self.env.ref("pms.open_pms_reservation_form_tree_all").read()[0]
        action["domain"] = [("id", "in", reservations.ids)]
        return action

    # ORM Overrides
    @api.model
    def create(self, vals):
        # TODO: Make sequence from property, not company
        if vals.get("name", _("New")) == _("New") or "name" not in vals:
            # TODO: change for property env variable
            pms_property_id = (
                self.env.user.pms_property_id.id
                if "pms_property_id" not in vals
                else vals["pms_property_id"]
            )
            vals["name"] = self.env["ir.sequence"].search(
                [("pms_property_id", "=", pms_property_id)]
            ).next_by_code("pms.folio") or _("New")
        result = super(PmsFolio, self).create(vals)
        return result

    # Business methods
    def action_done(self):
        reservation_ids = self.mapped("reservation_ids")
        for line in reservation_ids:
            if line.state == "onboard":
                line.action_reservation_checkout()

    def action_cancel(self):
        for folio in self:
            for reservation in folio.reservation_ids.filtered(
                lambda res: res.state != "cancelled"
            ):
                reservation.action_cancel()
            self.write(
                {
                    "state": "cancel",
                }
            )
        return True

    def action_confirm(self):
        for folio in self.filtered(
            lambda folio: folio.partner_id not in folio.message_partner_ids
        ):
            folio.message_subscribe([folio.partner_id.id])
        self.write({"state": "confirm", "confirmation_date": fields.Datetime.now()})
        # if self.env.context.get('send_email'):
        # self.force_quotation_send()

        # create an analytic account if at least an expense product
        # if any([expense_policy != 'no' for expense_policy in
        # self.sale_line_ids.mapped('product_id.expense_policy')]):
        # if not self.analytic_account_id:
        # self._create_analytic_account()
        return True

    # CHECKIN/OUT PROCESS

    def _compute_checkin_partner_count(self):
        for record in self:
            if record.reservation_type == "normal" and record.reservation_ids:
                filtered_reservs = record.reservation_ids.filtered(
                    lambda x: x.state != "cancelled"
                )
                mapped_checkin_partner = filtered_reservs.mapped(
                    "checkin_partner_ids.id"
                )
                record.checkin_partner_count = len(mapped_checkin_partner)
                mapped_checkin_partner_count = filtered_reservs.mapped(
                    lambda x: (x.adults + x.children) - len(x.checkin_partner_ids)
                )
                record.checkin_partner_pending_count = sum(mapped_checkin_partner_count)

    def _prepare_invoice(self):
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
            "partner_id": self.partner_invoice_id.id,
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

    def _get_invoice_grouping_keys(self):
        return ["company_id", "partner_id", "currency_id"]

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

    def _create_invoices(
        self,
        grouped=False,
        final=False,
        date=None,
        lines_to_invoice=False,
    ):
        """
        Create the invoice associated to the Folio.
        :param grouped: if True, invoices are grouped by Folio id.
        If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        :lines_to_invoice: invoice specific lines, if False, invoice all
        """
        if not self.env["account.move"].check_access_rights("create", False):
            try:
                self.check_access_rights("write")
                self.check_access_rule("write")
            except AccessError:
                return self.env["account.move"]

        # 1) Create invoices.
        if not lines_to_invoice:
            lines_to_invoice = self.sale_line_ids
        invoice_vals_list = self.get_invoice_vals_list(final, lines_to_invoice)

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
            .with_context(default_move_type="out_invoice")
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

    def get_invoice_vals_list(self, final=False, lines_to_invoice=False):
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
            invoice_vals = order._prepare_invoice()

            # Invoice line values (keep only necessary sections).
            invoice_lines_vals = []
            for line in order.sale_line_ids.filtered(
                lambda l: l.id in lines_to_invoice.ids
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
                        sequence=invoice_item_sequence
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
        for line in self.reservation_ids:
            price_reduce = line.price_total
            product = line.room_type_id.product_id
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
        for line in self.service_ids:
            price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
            taxes = line.tax_ids.compute_all(
                price_reduce, quantity=line.product_qty, product=line.product_id
            )["taxes"]
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

    # Check that only one sale channel is selected
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
                    ("property_id", "=", property_folio_id[0]),
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
                "property_id": property_folio_id[0],
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
            "statement_folio_ids": [(6, 0, folios.ids)],
            "reservation_ids": [(6, 0, reservation_ids)],
            "service_ids": [(6, 0, service_ids)],
            "payment_ref": folios.mapped("name"),
            "statement_id": statement.id,
            "journal_id": statement.journal_id.id,
            "counterpart_account_id": receivable_account.id,
        }
