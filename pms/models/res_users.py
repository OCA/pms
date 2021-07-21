# Copyright 2019 Pablo Quesada
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

import werkzeug

from odoo import _, api, fields, models
from odoo.exceptions import AccessDenied, ValidationError
from odoo.http import request

from ..pms_jwt.validator import validator

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    pms_property_id = fields.Many2one(
        string="Default Property",
        help="The property that is selected within " "those allowed for the user",
        comodel_name="pms.property",
        domain="[('id','in',pms_property_ids)]",
        context={"user_preference": True},
    )
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="The properties allowed for this user",
        comodel_name="pms.property",
        relation="pms_property_users_rel",
        column1="user_id",
        column2="pms_property_id",
        domain="[('company_id','in',company_ids)]",
    )

    access_token_ids = fields.One2many(
        string="Access Tokens",
        comodel_name="jwt_provider.access_token",
        inverse_name="user_id",
    )

    avatar = fields.Char(
        compute="_compute_avatar",
    )

    @api.model
    def get_active_property_ids(self):
        # TODO: Require performance test and security (dont allow any property id)
        # checks (Review lazy_property decorator?)
        user_property_ids = self.env.user.pms_property_ids.ids
        if request and request.httprequest.cookies.get("pms_pids"):
            active_property_ids = list(
                map(int, request.httprequest.cookies.get("pms_pids", "").split(","))
            )
            active_property_ids = [
                pid for pid in active_property_ids if pid in user_property_ids
            ]
            return self.env["pms.property"].browse(active_property_ids).ids
        return user_property_ids

    @api.constrains("pms_property_id", "pms_property_ids")
    def _check_property_in_allowed_properties(self):
        if any(user.pms_property_id not in user.pms_property_ids for user in self):
            raise ValidationError(
                _("The chosen property is not in the allowed properties for this user")
            )

    @api.constrains("pms_property_ids", "company_id")
    def _check_company_in_property_ids(self):
        for record in self:
            for pms_property in record.pms_property_ids:
                if pms_property.company_id not in record.company_ids:
                    raise ValidationError(
                        _("Some properties do not belong to the allowed companies")
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

    @api.depends()
    def _compute_avatar(self):
        base = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for u in self:
            u.avatar = werkzeug.urls.url_join(base, "web/avatar/%d" % u.id)

    def to_dict(self, single=False):
        res = []
        for u in self:
            d = u.read(["email", "name", "avatar", "company_id"])[0]
            res.append(d)

        return res[0] if single else res
