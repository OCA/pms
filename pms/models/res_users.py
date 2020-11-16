# Copyright 2019 Pablo Quesada
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import AccessError
from odoo.http import request


class ResUsers(models.Model):
    _inherit = "res.users"

    # Default Methods ang Gets
    @api.model
    def _get_default_pms_property(self):
        return self.env.user.pms_property_id

    # Fields declaration
    pms_property_id = fields.Many2one(
        "pms.property",
        string="Property",
        default=_get_default_pms_property,
        help="The property this user is currently working for.",
        context={"user_preference": True},
    )
    pms_property_ids = fields.Many2many(
        "pms.property",
        "pms_property_users_rel",
        "user_id",
        "pms_property_id",
        string="Properties",
        default=_get_default_pms_property,
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
            if any(pid not in user_property_ids for pid in active_property_ids):
                raise AccessError(_("Access to unauthorized or invalid properties."))
            return self.env["pms.property"].browse(active_property_ids).ids
        return user_property_ids
