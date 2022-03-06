# Copyright 2019 Pablo Quesada
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


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

    @api.model
    def get_active_property_ids(self):
        # TODO: Require performance test and security (dont allow any property id)
        # checks (Review lazy_property decorator?)
        user_property_ids = self.pms_property_ids.ids
        active_property_ids = self._context.get("allowed_pms_property_ids", [])
        if active_property_ids:
            if not self.env.su:
                user_property_ids = self.pms_property_ids.ids
                if any(pid not in user_property_ids for pid in active_property_ids):
                    raise AccessError(
                        _("Access to unauthorized or invalid properties.")
                    )
            return self.env["pms.property"].browse(active_property_ids).ids
        return self.pms_property_ids.ids

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
