# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    def send_mail(self, auto_commit=False):
        res = super(MailComposeMessage, self).send_mail(auto_commit=auto_commit)
        if (
            self._context.get("default_model") == "pms.folio"
            and self._context.get("active_model") == "pms.reservation"
        ):
            folio = self.env["pms.folio"].browse(self._context.get("default_res_id"))
            reservations = folio.reservation_ids
            for reservation in reservations:
                reservation.to_send_mail = False
        elif (
            self._context.get("default_model") == "pms.reservation"
            or self._context.get("default_model") == "pms.checkin.partner"
        ) and self._context.get("active_model") == "pms.reservation":
            reservation = self.env["pms.reservation"].browse(
                self._context.get("active_id")
            )
            reservation.to_send_mail = False
        elif (
            self._context.get("default_model") == "pms.checkin.partner"
            and self._context.get("active_model") == "pms.reservation"
        ):
            reservation = self.env["pms.reservation"].search(
                self._context.get("default_res_id")
            )
            reservation.to_send_mail = False
        return res
