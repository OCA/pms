from odoo import api, fields, models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"
    _order = "date desc, cash_turn desc, name desc, id desc"

    cash_turn = fields.Integer(
        string="Turn",
        help="Set the day turn of the cash statement",
        copy=False,
        readonly=True,
        compute="_compute_cash_turn",
        store=True,
    )

    @api.depends("journal_id", "pms_property_id", "date")
    def _compute_cash_turn(self):
        for record in self:
            if record.journal_id.type == "cash" and record.pms_property_id:
                day_statements = self.search(
                    [
                        ("journal_id.type", "=", "cash"),
                        ("pms_property_id", "=", record.pms_property_id.id),
                        ("date", "=", record.date),
                    ],
                    order="create_date asc",
                )
                record.cash_turn = list(day_statements).index(record) + 1

    def name_get(self):
        result = []
        for record in self:
            name = record.name
            if record.cash_turn:
                name += (
                    " [%s]" % str(record.cash_turn)
                    + " ("
                    + record.create_uid.name
                    + ")"
                )
            result.append((record.id, name))
        return result
