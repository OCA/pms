import logging

from odoo import _, api, fields, models
from odoo.exceptions import AccessDenied, ValidationError

from ..lib.validator import validator

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    access_token_ids = fields.One2many(
        string="Access Tokens",
        comodel_name="jwt_provider.access_token",
        inverse_name="user_id",
    )

    @classmethod
    def _login(cls, db, login, password, user_agent_env):
        user_id = super(ResUsers, cls)._login(db, login, password, user_agent_env)
        if user_id:
            return user_id
        uid = validator.verify(password)
        _logger.info(uid)
        return uid

    @api.model
    def _check_credentials(self, password, user_agent_env):
        try:
            super(ResUsers, self)._check_credentials(password, user_agent_env)
        except AccessDenied:
            if not validator.verify(password):
                raise

    def to_dict(self, single=False):
        res = []
        for u in self:
            d = u.read(["email", "name", "company_id"])[0]
            res.append(d)

        return res[0] if single else res
