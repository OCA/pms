# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    _check_pms_properties_auto = True

    # Fields declaration
    # TODO: REVIEW why not a Many2one?
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
        check_pms_properties=True,
    )
    origin_agency_id = fields.Many2one(
        string="Origin Agency",
        help="The agency where the folio account move originates",
        comodel_name="res.partner",
        domain="[('is_agency', '=', True)]",
        compute="_compute_origin_agency_id",
        store=True,
        readonly=False,
    )
    move_id = fields.Many2one(check_pms_properties=True)

    @api.depends("quantity")
    def _compute_name(self):
        for record in self:
            if record.folio_line_ids and not record.name_changed_by_user:
                record.name_changed_by_user = False
                record.name = self.env["folio.sale.line"].generate_folio_sale_name(
                    record.folio_line_ids.reservation_id,
                    record.product_id,
                    record.folio_line_ids.service_id,
                    record.folio_line_ids.reservation_line_ids,
                    record.folio_line_ids.service_line_ids,
                    qty=record.quantity,
                )

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
