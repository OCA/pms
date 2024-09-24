from odoo import api, models


class PmsReservation(models.Model):
    _inherit = "pms.reservation"

    @api.model
    def create(self, vals):
        result = super(PmsReservation, self).create(vals)
        result.access_token = result._portal_ensure_token()
        return result
