from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    availability_rule_field_ids = fields.Many2many(
        string="Availability Rules",
        help="Configurable availability rules",
        default=lambda self: self._default_avail_rule_fields(),
        comodel_name="ir.model.fields",
        relation="ir_model_fields_res_users_rel",
        column1="ir_model_fields",
        column2="res_users",
    )

    def _default_avail_rule_fields(self):
        default_avail_rule_fields = self.env["ir.model.fields"].search(
            [
                ("model_id", "=", "pms.availability.plan.rule"),
                ("name", "in", ("min_stay", "quota")),
            ]
        )
        if default_avail_rule_fields:
            return default_avail_rule_fields.ids
        else:
            return []
