from odoo import api, models


class PmsReservation(models.Model):
    _inherit = "pms.reservation"

    @api.model_create_multi
    def create(self, vals_list):
        records = super(PmsReservation, self).create(vals_list)
        for record in records:
            record._portal_ensure_token()
        return records
