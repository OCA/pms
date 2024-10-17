# Copyright 2019 Pablo Quesada
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.http import request


class ResUsers(models.Model):
    _inherit = "res.users"

    pms_property_id = fields.Many2one(
        string="Default Property",
        help="The property that is selected within " "those allowed for the user",
        comodel_name="pms.property",
        domain="[('id','in',pms_property_ids)]",
        context={"user_preference": True},
        index=True,
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

    def _is_property_member(self, pms_property_id):
        self.ensure_one()
        # TODO: Use pms_teams and roles to check if user is member of property
        # and analice the management of external users like a Call Center
        return self.env.user.has_group(
            "pms.group_pms_user"
        ) and not self.env.user.has_group("pms.group_pms_call")

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

    # Inherit Create and Write method to set context avoid_document_restriction
    @api.model
    def create(self, vals):
        return super(
            ResUsers, self.with_context(avoid_document_restriction=True)
        ).create(vals)

    def write(self, vals):
        return super(
            ResUsers, self.with_context(avoid_document_restriction=True)
        ).write(vals)
