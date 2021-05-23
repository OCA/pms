# Copyright 2021 Jose Luis Algara (Alda Hotels <https://www.aldahotels.es>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PmsRoom(models.Model):
    _inherit = "pms.reservation"

    dont_disturb = fields.Boolean(
        string="Dont disturb",
        default=False,
    )

    # def action_reservation_checkout(self):
    #     for record in self:
    #         if not record.allowed_checkout:
    #             raise UserError(_("This reservation cannot be check out"))
    #         record.state = "done"
    #         if record.checkin_partner_ids:
    #             record.checkin_partner_ids.filtered(
    #                 lambda check: check.state == "onboard"
    #             ).action_done()
    #     return True
