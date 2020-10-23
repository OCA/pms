# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models

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

    @api.model
    def _default_diff_invoicing(self):
        """
        If the guest has an invoicing address set,
        this method return diff_invoicing = True, else, return False
        """
        if "folio_id" in self.env.context:
            folio = self.env["pms.folio"].browse([self.env.context["folio_id"]])
        if folio.partner_id.id == folio.partner_invoice_id.id:
            return False
        return True

    @api.model
    def _get_default_pms_property(self):
        return (
            self.env.user.pms_property_id
        )  # TODO: Change by property env variable (like company)

    # Fields declaration
    name = fields.Char(
        string="Folio Number", readonly=True, index=True, default=lambda self: _("New")
    )
    pms_property_id = fields.Many2one(
        "pms.property", default=_get_default_pms_property, required=True
    )
    partner_id = fields.Many2one("res.partner", tracking=True, ondelete="restrict")
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
    company_id = fields.Many2one(
        "res.company",
        "Company",
        required=True,
        default=lambda self: self.env.company,
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
        "Agency",
        ondelete="restrict",
        domain=[("is_agency", "=", True)],
    )
    payment_ids = fields.One2many("account.payment", "folio_id", readonly=True)
    # return_ids = fields.One2many("payment.return", "folio_id", readonly=True)
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
    move_ids = fields.Many2many(
        "account.move",
        string="Invoices",
        compute="_compute_get_invoiced",
        readonly=True,
        copy=False,
        compute_sudo=True,
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
    channel_type = fields.Selection(
        [
            ("direct", "Direct"),
            ("agency", "Agency"),
        ],
        string="Sales Channel",
        compute="_compute_channel_type",
        store=True,
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
    booking_pending = fields.Integer(
        "Booking pending", compute="_compute_checkin_partner_count"
    )
    checkin_partner_count = fields.Integer(
        "Checkin counter", compute="_compute_checkin_partner_count"
    )
    checkin_partner_pending_count = fields.Integer(
        "Checkin Pending", compute="_compute_checkin_partner_count"
    )
    # Invoice Fields-----------------------------------------------------
    invoice_status = fields.Selection(
        [
            ("invoiced", "Fully Invoiced"),
            ("to invoice", "To Invoice"),
            ("no", "Nothing to Invoice"),
        ],
        string="Invoice Status",
        compute="_compute_get_invoiced",
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

    # Compute and Search methods
    @api.depends("reservation_ids", "reservation_ids.state")
    def _compute_number_of_rooms(self):
        for folio in self:
            folio.number_of_rooms = len(
                folio.reservation_ids.filtered(lambda a: a.state != "cancelled")
            )

    @api.depends("partner_id")
    def _compute_pricelist_id(self):
        for folio in self:
            pricelist_id = (
                folio.partner_id.property_product_pricelist
                and folio.partner_id.property_product_pricelist.id
                or self.env.user.pms_property_id.default_pricelist_id.id
            )
            if folio.pricelist_id.id != pricelist_id:
                # TODO: Warning change de pricelist?
                folio.pricelist_id = pricelist_id

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

    @api.depends("agency_id")
    def _compute_channel_type(self):
        for folio in self:
            if folio.agency_id:
                folio.channel_type = "agency"
            else:
                folio.channel_type = "direct"

    @api.depends("partner_id")
    def _compute_payment_term_id(self):
        self.payment_term_id = False
        for folio in self:
            folio.payment_term_id = (
                self.partner_id.property_payment_term_id
                and self.partner_id.property_payment_term_id.id
                or False
            )

    @api.depends(
        "state", "reservation_ids.invoice_status", "service_ids.invoice_status"
    )
    def _compute_get_invoiced(self):
        """
        Compute the invoice status of a Folio. Possible statuses:
        - no: if the Folio is not in status 'sale' or 'done', we
          consider that there is nothing to invoice.
          This is also the default value if the conditions of no other
          status is met.
        - to invoice: if any Folio line is 'to invoice',
          the whole Folio is 'to invoice'
        - invoiced: if all Folio lines are invoiced, the Folio is invoiced.

        The invoice_ids are obtained thanks to the invoice lines of the
        Folio lines, and we also search for possible refunds created
        directly from existing invoices. This is necessary since such a
        refund is not directly linked to the Folio.
        """
        for folio in self.filtered("pricelist_id"):
            move_ids = (
                folio.reservation_ids.mapped("move_line_ids")
                .mapped("move_id")
                .filtered(lambda r: r.type in ["out_invoice", "out_refund"])
            )
            invoice_ids = (
                folio.service_ids.mapped("move_line_ids")
                .mapped("move_id")
                .filtered(lambda r: r.type in ["out_invoice", "out_refund"])
            )
            # TODO: Search for invoices which have been 'cancelled'
            # (filter_refund = 'modify' in 'account.move.refund')
            # use like as origin may contains multiple references
            # (e.g. 'SO01, SO02')
            refunds = invoice_ids.search(
                [
                    ("invoice_origin", "like", folio.name),
                    ("company_id", "=", folio.company_id.id),
                ]
            ).filtered(lambda r: r.type in ["out_invoice", "out_refund"])
            invoice_ids |= refunds.filtered(lambda r: folio.id in r.folio_ids.ids)
            # Search for refunds as well
            refund_ids = self.env["account.move"].browse()
            if invoice_ids:
                for inv in invoice_ids:
                    refund_ids += refund_ids.search(
                        [
                            ("type", "=", "out_refund"),
                            ("invoice_origin", "=", inv.number),
                            ("invoice_origin", "!=", False),
                            ("journal_id", "=", inv.journal_id.id),
                        ]
                    )
            # Ignore the status of the deposit product
            deposit_product_id = self.env[
                "sale.advance.payment.inv"
            ]._default_product_id()
            service_invoice_status = [
                service.invoice_status
                for service in folio.service_ids
                if service.product_id != deposit_product_id
            ]
            reservation_invoice_status = [
                reservation.invoice_status for reservation in folio.reservation_ids
            ]

            if folio.state not in ("confirm", "done"):
                invoice_status = "no"
            elif any(
                invoice_status == "to invoice"
                for invoice_status in service_invoice_status
            ) or any(
                invoice_status == "to invoice"
                for invoice_status in reservation_invoice_status
            ):
                invoice_status = "to invoice"
            elif all(
                invoice_status == "invoiced"
                for invoice_status in service_invoice_status
            ) or any(
                invoice_status == "invoiced"
                for invoice_status in reservation_invoice_status
            ):
                invoice_status = "invoiced"
            else:
                invoice_status = "no"

            folio.update(
                {
                    "move_ids": move_ids.ids + refund_ids.ids,
                    "invoice_status": invoice_status,
                }
            )

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

    # TODO: Add return_ids to depends
    @api.depends("amount_total", "payment_ids", "reservation_type", "state")
    def _compute_amount(self):
        acc_pay_obj = self.env["account.payment"]
        for record in self:
            if record.reservation_type in ("staff", "out"):
                vals = {
                    "pending_amount": 0,
                    "invoices_paid": 0,
                    # "refund_amount": 0,
                }
                record.update(vals)
            else:
                total_inv_refund = 0
                payments = acc_pay_obj.search([("folio_id", "=", record.id)])
                total_paid = sum(pay.amount for pay in payments)
                # return_lines = self.env["payment.return.line"].search(
                #     [
                #         ("move_line_ids", "in", payments.mapped("move_line_ids.id")),
                #         ("return_id.state", "=", "done"),
                #     ]
                # )
                # total_inv_refund = sum(
                #   pay_return.amount for pay_return in return_lines
                # )
                total = record.amount_total
                # REVIEW: Must We ignored services in cancelled folios
                # pending amount?
                if record.state == "cancelled":
                    total = total - sum(record.service_ids.mapped("price_total"))
                vals = {
                    "pending_amount": total - total_paid + total_inv_refund,
                    "invoices_paid": total_paid,
                    # "refund_amount": total_inv_refund,
                }
                record.update(vals)

    # Action methods

    def action_pay(self):
        self.ensure_one()
        partner = self.partner_id.id
        amount = self.pending_amount
        view_id = self.env.ref("pms.account_payment_view_form_folio").id
        return {
            "name": _("Register Payment"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "account.payment",
            "type": "ir.actions.act_window",
            "view_id": view_id,
            "context": {
                "default_folio_id": self.id,
                "default_amount": amount,
                "default_payment_type": "inbound",
                "default_partner_type": "customer",
                "default_partner_id": partner,
                "default_communication": self.name,
            },
            "target": "new",
        }

    def open_moves_folio(self):
        invoices = self.mapped("move_ids")
        action = self.env.ref("account.action_move_out_invoice_type").read()[0]
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
            "target": "new",
        }

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
        # self.order_line.mapped('product_id.expense_policy')]):
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
