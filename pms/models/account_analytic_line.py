from odoo import api, fields, models


class AccountAnalyticDistribution(models.Model):
    _inherit = "account.analytic.distribution.model"

    pms_property_id = fields.Many2one(
        name="Property",
        comodel_name="pms.property",
        check_pms_properties=True,
        index=True,
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if "pms_property_id" in fields and self.env.context.get(
            "default_analytic_distribution"
        ):
            distribution = self.env.context["default_analytic_distribution"]
            if distribution.keys():
                property_ids = self.env["pms.property"].search(
                    [
                        (
                            "analytic_account_id",
                            "in",
                            [int(x) for x in distribution.keys()],
                        )
                    ]
                )
                if property_ids:
                    res["pms_property_id"] = property_ids[0].id
                    res["company_id"] = property_ids[0].company_id.id
        return res

    def _get_distribution(self, vals):
        pms_property_id = self.env.context.get("pms_property_id")
        if pms_property_id:
            vals["pms_property_id"] = pms_property_id
        res = super()._get_distribution(vals)
        return res
