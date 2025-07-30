# Copyright 2019 Pablo Quesada
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = "res.users"

    pms_property_id = fields.Many2one(
        comodel_name="pms.property",
        string="Default Property",
        domain="[('id', 'in', pms_property_ids)]",
        context={"user_preference": True},
        index=True,
        help="The property that is selected within those allowed for the user",
    )
    pms_property_ids = fields.Many2many(
        comodel_name="pms.property",
        relation="pms_property_users_rel",
        column1="user_id",
        column2="pms_property_id",
        string="Properties",
        domain="[('company_id','in',company_ids)]",
        help="The properties allowed for this user",
    )

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
    @api.model_create_multi
    def create(self, vals_list):
        return super(
            ResUsers, self.with_context(avoid_document_restriction=True)
        ).create(vals_list)

    def write(self, vals):
        return super(
            ResUsers, self.with_context(avoid_document_restriction=True)
        ).write(vals)
