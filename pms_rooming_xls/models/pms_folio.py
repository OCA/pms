# Copyright 2009-2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class PmsFolio(models.Model):
    _inherit = "pms.folio"

    def rooming_xls(self):
        checkins = self.checkin_partner_ids
        ctx = {
            "active_model": "pms.checkin.partner",
            "active_ids": checkins.ids,
        }
        report = checkins.with_context(ctx).rooming_xls()
        return report
