from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"
    _check_pms_properties_auto = True

    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        comodel_name="pms.property",
        ondelete="restrict",
        relation="account_journal_pms_property_rel",
        column1="account_journal_id",
        column2="pms_property_id",
        check_pms_properties=True,
    )
    allowed_pms_payments = fields.Boolean(
        string="For manual payments",
        help="Use to pay for reservations",
    )
