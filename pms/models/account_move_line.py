# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import _, api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    _check_pms_properties_auto = True

    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=False,
    )
    folio_line_ids = fields.Many2many(
        string="Folio Lines",
        help="The folio lines in the account move lines",
        copy=True,
        comodel_name="folio.sale.line",
        relation="folio_sale_line_invoice_rel",
        column1="invoice_line_id",
        column2="sale_line_id",
    )
    folio_ids = fields.Many2many(
        comodel_name="pms.folio",
        string="Folios",
        compute="_compute_folio_ids",
        store=True,
        check_pms_properties=True,
    )
    name_changed_by_user = fields.Boolean(
        string="Name set manually",
        help="""Techinal field to know if the name was set manually by the user
        or by the system. If the name was set manually, the system will not
        change it when the qty days are changed""",
        default=True,
    )
    pms_property_id = fields.Many2one(
        name="Property",
        comodel_name="pms.property",
        compute="_compute_pms_property_id",
        store=True,
        readonly=False,
        index=True,
        check_pms_properties=True,
    )
    origin_agency_id = fields.Many2one(
        string="Origin Agency",
        help="The agency where the folio account move originates",
        comodel_name="res.partner",
        domain="[('is_agency', '=', True)]",
        compute="_compute_origin_agency_id",
        store=True,
        index=True,
        readonly=False,
    )
    move_id = fields.Many2one(check_pms_properties=True)

    @api.depends("account_id", "partner_id", "product_id", "pms_property_id")
    def _compute_analytic_distribution(self):
        properties = self.mapped("pms_property_id")
        if not properties:
            super()._compute_analytic_distribution()
        for pms_property in properties:
            records = self.filtered(
                lambda x, pmsp=pms_property: x.pms_property_id == pmsp
            )
            records = records.with_context(pms_property_id=pms_property.id)
            super(AccountMoveLine, records)._compute_analytic_distribution()
        return

    @api.depends("move_id.payment_reference", "quantity")
    def _compute_name(self):
        res = super()._compute_name()
        for record in self:
            if record.folio_line_ids and not record.name:
                record.name = self.env["folio.sale.line"].generate_folio_sale_name(
                    record.folio_line_ids.reservation_id,
                    record.product_id,
                    record.folio_line_ids.service_id,
                    record.folio_line_ids.reservation_line_ids,
                    record.folio_line_ids.service_line_ids,
                    qty=record.quantity,
                )
        return res

    @api.depends("move_id")
    def _compute_pms_property_id(self):
        for rec in self:
            if rec.move_id and rec.move_id.pms_property_id:
                rec.pms_property_id = rec.move_id.pms_property_id
            elif not rec.pms_property_id:
                rec.pms_property_id = False

    @api.depends(
        "folio_line_ids",
        "payment_id",
        "payment_id.folio_ids",
        "statement_line_id",
        "statement_line_id.folio_ids",
    )
    def _compute_folio_ids(self):
        if self.folio_line_ids:
            self.folio_ids = self.folio_line_ids.mapped("folio_id")
        elif self.payment_id:
            self.folio_ids = self.payment_id.folio_ids
        elif self.statement_line_id:
            self.folio_ids = self.statement_line_id.folio_ids
        else:
            self.folio_ids = False

    @api.depends("folio_line_ids")
    def _compute_origin_agency_id(self):
        """
        Compute the origin agency of the account move line,
        if the line has multiple agencies in origin,
        (p.e. nights with different agencies in origin),
        the first one is returned (REVIEW: is this correct?)
        """
        self.origin_agency_id = False
        for line in self:
            agencies = line.mapped("folio_line_ids.origin_agency_id")
            if agencies:
                line.origin_agency_id = agencies[0]

    def reconcile(self):
        """
        Reconcile the account move
        """
        # Update partner in payments and statement lines
        res = super().reconcile()
        for record in self:
            if record.payment_id:
                old_payment_partner = record.payment_id.partner_id
                new_payment_partner = record.payment_id.mapped(
                    "reconciled_invoice_ids.partner_id"
                )
                if (
                    old_payment_partner != new_payment_partner
                    and len(new_payment_partner) == 1
                ):
                    record.payment_id.partner_id = new_payment_partner
                    if old_payment_partner:
                        record.payment_id.message_post(
                            body=_(
                                "Partner modify automatically from"
                                " invoice: {old_partner} to {new_partner}"
                            ).format(
                                old_partner=old_payment_partner.name,
                                new_partner=new_payment_partner.name,
                            )
                        )
            if record.statement_line_id:
                old_statement_partner = record.statement_line_id.partner_id
                new_payment_partner = record.payment_id.mapped(
                    "reconciled_invoice_ids.partner_id"
                )
                if (
                    old_statement_partner != new_payment_partner
                    and len(new_payment_partner) == 1
                ):
                    record.statement_line_id.partner_id = new_payment_partner
                    if old_statement_partner:
                        record.statement_line_id.message_post(
                            body=_(
                                "Partner modify automatically from "
                                "invoice: {old_partner} to {new_partner}"
                            ).format(
                                old_partner=old_statement_partner.name,
                                new_partner=new_payment_partner.name,
                            )
                        )
        return res

    def _get_lock_date_protected_fields(self):
        """Inherited from account.move.line
        to avoid to lock partner_id in reconciliation_fnames
        """
        lock_types = super()._get_lock_date_protected_fields()
        reconciliation_fnames = lock_types.get("reconciliation", [])
        # Remove partner_id from reconciliation_fnames
        # because it is not a protected field
        if "partner_id" in reconciliation_fnames:
            reconciliation_fnames.remove("partner_id")
        return {
            "tax": lock_types.get("tax", []),
            "fiscal": lock_types.get("fiscal", []),
            "reconciliation": reconciliation_fnames,
        }
