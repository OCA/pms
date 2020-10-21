# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    def send_mail(self, auto_commit=False):
        if (
            self._context.get("default_model") == "pms.folio"
            and self._context.get("default_res_id")
            and self._context.get("mark_so_as_sent")
        ):
            # TODO: WorkFlow Mails
            folio = self.env["pms.folio"].browse([self._context["default_res_id"]])
            if folio:
                cmds = [
                    (1, lid, {"to_send": False}) for lid in folio.reservation_ids.ids
                ]
                if any(cmds):
                    folio.reservation_ids = cmds
        return super(MailComposeMessage, self).send_mail(auto_commit=auto_commit)
