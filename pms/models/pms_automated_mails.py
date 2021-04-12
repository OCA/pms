from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PmsAutomatedMails(models.Model):
    _name = "pms.automated.mails"
    _description = "Automatic Mails"

    name = fields.Char(string="Name")

    pms_property_id = fields.Many2one(string="Property", comodel_name="pms.property")

    reservation_id = fields.Many2one(
        string="Reservations",
        comodel_name="pms.reservation",
    )
    automated_actions_id = fields.Many2one(
        string="Automated Actions", comodel_name="base.automation", ondelete="cascade"
    )

    time = fields.Integer(string="Time")

    time_type = fields.Selection(
        string="Time Range",
        selection=[
            ("minutes", "Minutes"),
            ("hour", "Hour"),
            ("day", "Days"),
            ("month", "Months"),
        ],
        default="day",
    )
    template_id = fields.Many2one(
        string="Template", comodel_name="mail.template", required=True
    )

    model_id = fields.Many2one(
        string="Model", comodel_name="ir.model", compute="_compute_model_id", store=True
    )

    reservation_date_fields_id = fields.Many2one(
        string="Action",
        comodel_name="ir.model.fields",
    )

    action = fields.Selection(
        string="Action",
        selection=[
            ("creation", "Reservation creation"),
            ("write", "Reservation modification"),
            ("cancel", "Reservation cancellation"),
            ("checkin", "Checkin"),
            ("checkout", "Checkout"),
            ("payment", "Payment"),
            ("invoice", "Invoice"),
        ],
        default="creation",
        required=True,
    )

    trigger = fields.Char(
        string="Trigger",
    )

    moment = fields.Selection(
        string="Moment",
        selection=[
            ("before", "Before"),
            ("after", "After"),
            ("in_act", "In the act"),
        ],
        default="before",
    )

    active = fields.Boolean(string="Active", default=True)

    @api.model
    def create(self, vals):
        name = vals.get("name")
        action = vals.get("action")
        model_field = vals.get("reservation_date_fields_id")
        time = vals.get("time")
        moment = vals.get("moment")
        date_range_type = vals.get("time_type")
        template_id = vals.get("template_id")
        active = vals.get("active")
        model_id = False
        trigger = "on_time"
        filter_domain = False
        if action == "creation":
            if moment == "before":
                raise UserError(_("The moment for this action cannot be 'Before'"))
            model_field = self.env["ir.model.fields"].search(
                [("model", "=", "pms.reservation"), ("name", "=", "date_order")]
            )
            filter_domain = [("date_order", "=", fields.Date.today())]
        if action in ("creation", "write", "cancellation", "checkin", "checkout"):
            model_id = self.env["ir.model"].search([("name", "=", "Reservation")])
        elif action == "payment":
            model_id = self.env["ir.model"].search([("name", "=", "Payments")])
        action_server_vals = {
            "name": name,
            "state": "email",
            "usage": "ir_cron",
            "model_id": model_id.id,
        }
        action_server = self.env["ir.actions.server"].create(action_server_vals)

        automated_actions_vals = {
            "active": active,
            "action_server_id": action_server.id,
            "trigger": trigger,
            "trg_date_id": model_field.id,
            "filter_domain": filter_domain,
            "trg_date_range": time,
            "trg_date_range_type": date_range_type,
            "template_id": template_id,
        }
        automated_action = self.env["base.automation"].create(automated_actions_vals)
        self.automated_actions_id = automated_action.id
        return super(PmsAutomatedMails, self).create(vals)
