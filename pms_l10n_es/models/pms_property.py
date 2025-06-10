from odoo import fields, models


class PmsProperty(models.Model):
    _inherit = "pms.property"

    institution = fields.Selection(
        [
            ("ses", "SES"),
        ],
        help="Institution to send daily guest data.",
        required=False,
    )
    institution_property_id = fields.Char(
        help="Id provided by institution to send data from property.",
    )
    ses_url = fields.Char(
        help="URL to send the data to SES",
    )
    institution_user = fields.Char(
        help="User provided by institution to send the data."
    )
    institution_password = fields.Char(
        help="Password provided by institution to send the data.",
    )
    institution_lessor_id = fields.Char(
        help="Id provided by institution to send data from lessor.",
    )
    ine_tourism_number = fields.Char(
        "Tourism number",
        help="Registration number in the Ministry of Tourism. Used for INE statistics.",
    )
    ine_seats = fields.Integer(
        string="Beds available excluding extra beds",
        default=0,
        help="Used for INE statistics.",
    )
    ine_permanent_staff = fields.Integer(
        string="Permanent Staff", default=0, help="Used for INE statistics."
    )
    ine_eventual_staff = fields.Integer(
        string="Eventual Staff", default=0, help="Used for INE statistics."
    )
    ine_unpaid_staff = fields.Integer(
        string="Unpaid Staff", default=0, help="Used for INE statistics."
    )
    ine_category_id = fields.Many2one(
        comodel_name="pms.ine.tourism.type.category",
        help="Hotel category in the Ministry of Tourism. Used for INE statistics.",
    )
    spanish_tourism_classification_id = fields.Many2one(
        comodel_name="pms.tourism.classification",
        string="Spanish Tourism Classification",
        help="Spanish tourism classification.",
    )
