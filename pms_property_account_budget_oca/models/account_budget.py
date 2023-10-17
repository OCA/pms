# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models

from_string = fields.Datetime.from_string


# ---------------------------------------------------------
# Budgets
# ---------------------------------------------------------


class CrossoveredBudget(models.Model):
    _inherit = "crossovered.budget"
    _check_pms_properties_auto = True

    pms_property_id = fields.Many2one(
        name="Property",
        comodel_name="pms.property",
        check_pms_properties=True,
    )


class CrossoveredBudgetLines(models.Model):
    _name = "crossovered.budget.lines"
    _description = "Budget Line"

    pms_property_id = fields.Many2one(
        name="Property",
        comodel_name="pms.property",
        related="general_budget_id.pms_property_id",
        store=True,
    )

    def _compute_practical_amount(self):
        for line in self:
            if line.pms_property_id:
                result = 0.0
                acc_ids = line.general_budget_id.account_ids.ids
                date_to = line.date_to
                date_from = line.date_from
                if line.analytic_account_id.id:
                    self.env.cr.execute(
                        """
                        SELECT SUM(amount)
                        FROM account_analytic_line
                        WHERE account_id=%s
                            AND (date between %s
                            AND %s)
                            AND general_account_id=ANY(%s)
                            AND pms_property_id=%s""",
                        (
                            line.analytic_account_id.id,
                            date_from,
                            date_to,
                            acc_ids,
                            line.pms_property_id.id,
                        ),
                    )
                    result = self.env.cr.fetchone()[0] or 0.0
                line.practical_amount = result
            else:
                super(CrossoveredBudgetLines, self)._compute_practical_amount()
