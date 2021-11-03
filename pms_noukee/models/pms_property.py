import requests

from odoo import fields, models


class PmsProperty(models.Model):

    _inherit = "pms.property"
    noukee_site_id = fields.Char(string="Noukee Site Id")
    noukee_user_id = fields.Char(string="Noukee user id")
    noukee_password = fields.Char(string="Noukee password")

    noukee_jwt = fields.Char(compute="_compute_noukee_jwt")

    def _compute_noukee_jwt(self):
        for record in self:
            response_login = requests.get(
                "https://cloud.noukee.com/api/v1/login?"
                + "clientId="
                + record.noukee_user_id
                + "&clientSecret="
                + record.noukee_password
            )

            record.noukee_jwt = response_login.json()["token"]
