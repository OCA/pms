from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"
    _check_pms_properties_auto = True

    pms_property_id = fields.Many2one(
        name="Property",
        comodel_name="pms.property",
        compute="_compute_pms_property_id",
        store=True,
        readonly=False,
        check_pms_properties=True,
    )

    @api.depends("move_id")
    def _compute_pms_property_id(self):
        for rec in self:
            if rec.move_id and rec.move_id.pms_property_id:
                rec.pms_property_id = rec.move_id.pms_property_id
            elif not rec.pms_property_id:
                rec.pms_property_id = False


class AccountAnalyticDistribution(models.Model):
    _inherit = "account.analytic.distribution"

    pms_property_id = fields.Many2one(
        name="Property",
        comodel_name="pms.property",
        check_pms_properties=True,
    )
