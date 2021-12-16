# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    @api.model
    def default_get(self, fields):
        res = super(MailComposeMessage, self).default_get(fields)
        template = self.env["mail.template"].browse(self._context.get("template_id"))
        res.update(
            {
                "composition_mode": "comment",
                "attachment_ids": False,
                "template_id": template.id,
            }
        )
        return res

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
