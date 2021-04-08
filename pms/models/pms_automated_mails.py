from odoo import fields, models, api


class PmsAutomatedMails(models.Model):
    _name = 'pms.automated.mails'
    _description = 'Automatic Mails'

    name = fields.Char(
        string="Name"
    )

    pms_property_id = fields.Many2one(
        string="Property",
        comodel_name="pms.property"
    )

    automated_actions_id = fields.Many2one(
        string="Automated Actions",
        comodel_name="base.automation"
    )

    time = fields.Integer(
        string="Time",
        required=True
    )

    time_type = fields.Selection(
        string="Time Range",
        selection=[
            ("minutes", "Minutes"),
            ("hour", "Hour"),
            ("day", "Days"),
            ("month", "Months")
        ],
        default="day",
        required=True
    )
    template_id = fields.Many2one(
        string="Template",
        comodel_name="mail.template",
        required=True
    )

    reservation_date_fields_id = fields.Many2one(
        string="Action",
        comodel_name="ir.model.fields",
        domain="[('model', '=', 'pms.reservation'),('ttype', 'in', ('date', 'datetime'))]"
    )
    @api.model
    def create(self, vals):
        name = vals.get("name")
        model_id = self.env["ir.model"].search([("name", "=", "Reservation")])
        action_server_vals = {
            "name": name,
            "state": "email",
            "usage": "ir_cron",
            "model_id": model_id.id,
        }
        action_server = self.env["ir.actions.server"].create(action_server_vals)
        model_field = vals.get("reservation_date_fields_id")
        time = vals.get("time")
        date_range_type = vals.get("time_type")
        template_id = vals.get("template_id")
        automated_actions_vals = {
            "action_server_id": action_server.id,
            "trigger": "on_time",
            "filter_domain": [("checkin", "<", "2021-12-31")],
            "trg_date_id": model_field.id,
            "trg_date_range": time,
            "trg_date_range_type": date_range_type,
            "template_id": template_id
        }
        self.env["base.automation"].create(automated_actions_vals)
        return super(PmsAutomatedMails, self).create(vals)
