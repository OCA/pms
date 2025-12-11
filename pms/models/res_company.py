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

    url_advert = fields.Char(help="Url to identify the ad")

    privacy_policy = fields.Html(
        help="Authorization by the user for the" "manage of their personal data",
    )

    check_min_partner_data_invoice = fields.Boolean(
        string="Check minimum partner data for invoices",
        help="""Check minimum partner data for invoices:
            - VAT, name, street, city, country""",
        default=False,
    )
    cancel_penalty_product_id = fields.Many2one(
        string="Cancel penalty product",
        help="Product used to calculate the cancel penalty",
        comodel_name="product.product",
        index=True,
        ondelete="restrict",
    )
