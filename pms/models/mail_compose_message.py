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
        # if (
        #     self._context.get("default_model") == "pms.folio"
        #     and self._context.get("default_res_id")
        #     and self._context.get("mark_so_as_sent")
        # ):
        #     # TODO: WorkFlow Mails
        #     folio = self.env["pms.folio"].browse([self._context["default_res_id"]])
        #     if folio:
        #         cmds = [
        #             (1, lid, {"to_send": False}) for lid in folio.reservation_ids.ids
        #         ]
        #         if any(cmds):
        #             folio.reservation_ids = cmds
        res = super(MailComposeMessage, self).send_mail(auto_commit=auto_commit)
        if self._context.get("record_id"):
            reservation = self.env["pms.reservation"].search(
                [("id", "=", self._context.get("record_id"))]
            )
            reservation.is_mail_send = True
        return res
