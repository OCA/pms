# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    pms_property_ids = fields.One2many(
        comodel_name="pms.property",
        inverse_name="company_id",
        string="Properties",
        help="Properties with access to the element",
    )
    privacy_policy = fields.Html(
        help="Authorization by the user for the manage of their personal data",
    )
    check_min_partner_data_invoice = fields.Boolean(
        default=False,
        string="Check minimum partner data for invoices",
        help="""Check minimum partner data for invoices:
            - VAT, name, street, city, country""",
    )
    pms_invoice_downpayment_policy = fields.Selection(
        selection=[
            ("no", "Manual"),
            ("all", "All"),
            ("checkout_past_month", "Checkout past month"),
        ],
        default="no",
        string="Downpayment policy invoce",
        help="""
            - Manual: Downpayment invoice will be created manually
            - All: Downpayment invoice will be created automatically
            - Current Month: Downpayment invoice will be created automatically
                only for reservations with checkout date past of current month
            """,
    )
    document_partner_required = fields.Boolean(
        default=False,
        help="""If true, the partner document is required
        to create a new contact""",
    )
    cancel_penalty_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Cancel penalty product",
        index=True,
        ondelete="restrict",
        help="Product used to calculate the cancel penalty",
    )
    self_billed_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Self billed journal",
        help="Journal used to create self billing",
        index=True,
        ondelete="restrict",
    )
    self_billed_tax_ids = fields.Many2many(
        comodel_name="account.tax",
        relation="company_autoinvoicing_tax_rel",
        column1="company_id",
        column2="tax_id",
        string="Self billed taxes",
        domain="[('company_id', '=', id)]",
        help="Taxes used to create self billing",
    )
