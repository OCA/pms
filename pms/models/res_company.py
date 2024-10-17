# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    pms_property_ids = fields.One2many(
        string="Properties",
        help="Properties with access to the element",
        comodel_name="pms.property",
        inverse_name="company_id",
    )

    url_advert = fields.Char(string="Url Advert", help="Url to identify the ad")

    privacy_policy = fields.Html(
        string="Privacy Policy",
        help="Authorization by the user for the" "manage of their personal data",
    )

    check_min_partner_data_invoice = fields.Boolean(
        string="Check minimum partner data for invoices",
        help="""Check minimum partner data for invoices:
            - VAT, name, street, city, country""",
        default=False,
    )

    pms_invoice_downpayment_policy = fields.Selection(
        selection=[
            ("no", "Manual"),
            ("all", "All"),
            ("checkout_past_month", "Checkout past month"),
        ],
        string="Downpayment policy invoce",
        help="""
            - Manual: Downpayment invoice will be created manually
            - All: Downpayment invoice will be created automatically
            - Current Month: Downpayment invoice will be created automatically
                only for reservations with checkout date past of current month
            """,
        default="no",
    )

    document_partner_required = fields.Boolean(
        string="Document partner required",
        help="""If true, the partner document is required
        to create a new contact""",
        default=False,
    )

    cancel_penalty_product_id = fields.Many2one(
        string="Cancel penalty product",
        help="Product used to calculate the cancel penalty",
        comodel_name="product.product",
        index=True,
        ondelete="restrict",
    )
