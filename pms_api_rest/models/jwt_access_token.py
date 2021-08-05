from datetime import datetime

from odoo import api, fields, models


class JwtAccessToken(models.Model):
    _name = "jwt_provider.access_token"
    _description = "Store user access token for one-time-login"

    token = fields.Char("Access Token", required=True)
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        required=True,
        ondelete="cascade",
    )
    expires = fields.Datetime(
        "Expires",
        required=True,
    )

    is_expired = fields.Boolean(
        compute="_compute_is_expired",
    )

    @api.depends("expires")
    def _compute_is_expired(self):
        for token in self:
            token.is_expired = datetime.now() > token.expires
