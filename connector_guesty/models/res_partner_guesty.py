# Copyright (C) 2021 Casai (https://www.casai.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import fields, models

_log = logging.getLogger(__name__)


class ResPartnerGuesty(models.Model):
    _name = "res.partner.guesty"
    _description = "Guesty Partner"

    partner_id = fields.Many2one("res.partner", required=True, ondelete="cascade")
    guesty_id = fields.Char(required=True)

    def guesty_push_update(self):
        first_name, last_name = self.partner_id.split_name()

        body = {
            "firstName": first_name,
            "lastName": last_name,
            "fullName": self.partner_id.name,
        }

        if self.partner_id.phone:
            body["phone"] = self.partner_id.phone

        if self.partner_id.email:
            body["email"] = self.partner_id.email

        success, res = self.env.company.guesty_backend_id.call_put_request(
            url_path="guests/{}".format(self.guesty_id), body=body
        )

        if success:
            return res
