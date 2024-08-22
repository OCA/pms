import uuid

from odoo import api, fields, models
from odoo.tools.safe_eval import time


class PmsFolio(models.Model):
    _inherit = "pms.folio"
    api_rest_id = fields.Char(string="API Rest ID", help="API Rest ID")

    pms_api_log_ids = fields.Many2many(
        string="API Logs",
        help="API Logs",
        comodel_name="pms.api.log",
        relation="pms_folio_pms_api_log_rel",
        column1="folio_ids",
        column2="pms_api_log_ids",
    )
