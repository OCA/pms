from odoo import fields, models


class PmsFolio(models.Model):
    _inherit = "pms.folio"

    pms_api_log_ids = fields.Many2many(
        string="API Logs",
        help="API Logs",
        comodel_name="pms.api.log",
        relation="pms_folio_pms_api_log_rel",
        column1="folio_ids",
        column2="pms_api_log_ids",
    )
