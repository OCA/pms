from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PmsAutomatedMails(models.Model):
    _name = "pms.automated.mails"
    _description = "Automatic Mails"

    name = fields.Char(string="Name", required=True)

    pms_property_id = fields.Many2one(string="Property", comodel_name="pms.property")

    automated_actions_id = fields.Many2one(
        string="Automated Actions",
        comodel_name="base.automation",
        ondelete="cascade",
        store=True,
        readonly=False,
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
        time = vals.get("time")
        date_range_type = vals.get("time_type")
        template_id = vals.get("template_id")
        active = vals.get("active")
        moment = vals.get("moment")
        dict_val = self._prepare_automated_actions_id(action, time, moment)
        action_server_vals = {
            "name": name,
            "state": "email",
            "usage": "ir_cron",
            "model_id": dict_val["model_id"].id,
        }
        action_server = self.env["ir.actions.server"].create(action_server_vals)
        model_field = dict_val["model_field"]
        if not model_field:
            automated_actions_vals = {
                "active": active,
                "action_server_id": action_server.id,
                "trigger": dict_val["trigger"],
                "filter_domain": dict_val["filter_domain"],
                "trg_date_range": dict_val["time"],
                "trg_date_range_type": date_range_type,
                "template_id": template_id,
            }
        else:
            automated_actions_vals = {
                "active": active,
                "action_server_id": action_server.id,
                "trigger": dict_val["trigger"],
                "trg_date_id": dict_val["model_field"].id,
                "filter_domain": dict_val["filter_domain"],
                "trg_date_range": dict_val["time"],
                "trg_date_range_type": date_range_type,
                "template_id": template_id,
            }
        automated_action = self.env["base.automation"].create(automated_actions_vals)
        vals.update({"automated_actions_id": automated_action.id})
        return super(PmsAutomatedMails, self).create(vals)

    def write(self, vals):
        result = super(PmsAutomatedMails, self).write(vals)
        dict_val = self._prepare_automated_actions_id(
            self.action, self.time, self.moment
        )
        automated_actions_id = self.automated_actions_id
        action_server = automated_actions_id.action_server_id
        action_server_vals = {
            "name": self.name,
            "state": "email",
            "usage": "ir_cron",
            "model_id": dict_val["model_id"].id,
        }
        action_server.write(action_server_vals)
        model_field = dict_val["model_field"]
        if not model_field:
            automated_actions_vals = {
                "active": self.active,
                "action_server_id": action_server.id,
                "trigger": dict_val["trigger"],
                "filter_domain": dict_val["filter_domain"],
                "trg_date_range": dict_val["time"],
                "trg_date_range_type": self.time_type,
                "template_id": self.template_id,
            }
        else:
            automated_actions_vals = {
                "active": self.active,
                "action_server_id": action_server.id,
                "trigger": dict_val["trigger"],
                "trg_date_id": dict_val["model_field"].id,
                "filter_domain": dict_val["filter_domain"],
                "trg_date_range": dict_val["time"],
                "trg_date_range_type": self.time_type,
                "template_id": self.template_id,
            }
        automated_actions_id.write(automated_actions_vals)
        vals.update({"automated_actions_id": automated_actions_id.id})
        return result

    def unlink(self):
        automated_actions_id = self.automated_actions_id
        action_server = automated_actions_id.action_server_id
        automated_actions_id.unlink()
        action_server.unlink()
        return super(PmsAutomatedMails, self).unlink()

    def _prepare_automated_actions_id(self, action, time, moment):
        trigger = False
        model_field = False
        filter_domain = False
        model_id = False
        today = fields.Date.today()
        if action in ("creation", "write", "cancel") and moment == "before":
            raise UserError(_("The moment for this action cannot be 'Before'"))
        # action: create reservation
        if action == "creation":
            model_id = self.env["ir.model"].search([("name", "=", "Reservation")])
            if moment == "in_act":
                trigger = "on_create"
                time = 0
            else:
                trigger = "on_time"
                model_field = self.env["ir.model.fields"].search(
                    [("model", "=", "pms.reservation"), ("name", "=", "create_date")]
                )
        # action: write and cancel reservation
        if action == "write" or action == "cancel":
            model_id = self.env["ir.model"].search([("name", "=", "Reservation")])
            if action == "cancel":
                filter_domain = [("state", "=", "cancelled")]
            if moment == "in_act":
                trigger = "on_write"
                time = 0
            else:
                trigger = "on_time"
                model_field = self.env["ir.model.fields"].search(
                    [("model", "=", "pms.reservation"), ("name", "=", "write_date")]
                )
        # action: checkin
        if action == "checkin":
            model_id = self.env["ir.model"].search([("name", "=", "Reservation")])
            trigger = "on_time"
            model_field = self.env["ir.model.fields"].search(
                [("model", "=", "pms.reservation"), ("name", "=", "checkin")]
            )
            if moment == "in_act":
                time = 0
                filter_domain = [("checkin", "=", str(today))]
            elif moment == "before":
                time = time * (-1)
        # action: checkout
        if action == "checkout":
            model_id = self.env["ir.model"].search([("name", "=", "Reservation")])
            trigger = "on_time"
            model_field = self.env["ir.model.fields"].search(
                [("model", "=", "pms.reservation"), ("name", "=", "checkout")]
            )
            if moment == "in_act":
                time = 0
                filter_domain = [("checkout", "=", str(today))]
            elif moment == "before":
                time = time * (-1)
        # action: payments
        if action == "payment":
            model_id = self.env["ir.model"].search(
                [("name", "=", "Payments"), ("transient", "=", False)]
            )
            if moment == "in_act":
                trigger = "on_creation"
                model_field = self.env["ir.model.fields"].search(
                    [("model", "=", "account.payment"), ("name", "=", "create_date")]
                )
                time = 0
            else:
                trigger = "on_time"
                model_field = self.env["ir.model.fields"].search(
                    [("model", "=", "account.payment"), ("name", "=", "date")]
                )
                if moment == "before":
                    time = time * (-1)
        result = {
            "trigger": trigger,
            "model_field": model_field,
            "filter_domain": filter_domain,
            "time": time,
            "model_id": model_id,
        }
        return result
