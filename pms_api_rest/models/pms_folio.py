from odoo import fields, models


class PmsFolio(models.Model):
    _name = "pms.folio"

    pms_api_log_id = fields.Many2one(
        string="PMS API Log",
        help="PMS API Log",
        comodel_name="pms.api.log",
    )
    origin_json = fields.Text(
        string="Origin JSON",
        help="Origin JSON",
    )
