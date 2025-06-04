from odoo import api, fields, models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"
    _check_pms_properties_auto = True

    pms_property_id = fields.Many2one(
        string="Property",
        help="Properties with access to the element",
        comodel_name="pms.property",
        readonly=False,
        compute="_compute_pms_property_id",
        store=True,
        copy=False,
        index=True,
        check_pms_properties=True,
    )
    journal_id = fields.Many2one(
        readonly=False,
        check_pms_properties=True,
    )

    @api.depends("journal_id")
    def _compute_pms_property_id(self):
        for record in self:
            if len(record.journal_id.pms_property_ids) == 1:
                record.pms_property_id = record.journal_id.pms_property_ids[0]
            elif not record.pms_property_id:
                record.pms_property_id = False
