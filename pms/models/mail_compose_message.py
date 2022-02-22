# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    def send_mail(self, auto_commit=False):
        res = super(MailComposeMessage, self).send_mail(auto_commit=auto_commit)
        if self._context.get("record_id"):
            folio = self.env["pms.folio"].search(
                [("id", "=", self._context.get("record_id"))]
            )
            reservations = folio.reservation_ids
            for reservation in reservations:
                reservation.to_send_mail = False
        return res
