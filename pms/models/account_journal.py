from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    pms_property_ids = fields.Many2many("pms.property", string="Property", copy=False)

    @api.constrains("pms_property_ids", "company_id")
    def _check_property_company_integrity(self):
        for rec in self:
            if rec.company_id and rec.pms_property_ids:
                property_companies = rec.pms_property_ids.mapped("company_id")
                if len(property_companies) > 1 or rec.company_id != property_companies:
                    raise UserError(
                        _(
                            "The company of the properties must match "
                            "the company on account journal"
                        )
                    )
