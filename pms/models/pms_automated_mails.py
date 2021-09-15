from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PmsAutomatedMails(models.Model):
    _name = "pms.automated.mails"
    _description = "Automatic Mails"

    name = fields.Char(string="Name", help="Name of the automated mail.", required=True)

    pms_property_ids = fields.Many2many(
        string="Property",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        comodel_name="pms.property",
    )

    automated_actions_id = fields.Many2one(
        string="Automated Actions",
        help="automated action that is created when creating automated emails ",
        comodel_name="base.automation",
    )

    time = fields.Integer(string="Time", help="Amount of time")

    time_type = fields.Selection(
        string="Time Range",
        help="Type of date range",
        selection=[
            ("minutes", "Minutes"),
            ("hour", "Hour"),
            ("day", "Days"),
            ("month", "Months"),
        ],
        default="day",
    )
    template_id = fields.Many2one(
        string="Template",
        help="The template that will be sent by email",
        comodel_name="mail.template",
        required=True,
    )

    action = fields.Selection(
        string="Action",
        help="The action that will cause the email to be sent ",
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
        help="Moment in relation to the action in which the email will be sent",
        selection=[
            ("before", "Before"),
            ("after", "After"),
            ("in_act", "In the act"),
        ],
        default="before",
    )

    active = fields.Boolean(
        string="Active", help="Indicates if the automated mail is active", default=True
    )

    @api.model
    def create(self, vals):
        name = vals.get("name")
        action = vals.get("action")
        time = vals.get("time")
        date_range_type = vals.get("time_type")
        template_id = vals.get("template_id")
        active = vals.get("active")
        moment = vals.get("moment")
        properties = vals.get("pms_property_ids")
        is_create = True
        if action in ("creation", "write", "cancel", "invoice") and moment == "before":
            raise UserError(_("The moment for this action cannot be 'Before'"))
        dict_val = self._prepare_automated_actions_id(
            action, time, moment, properties, is_create
        )
        action_server_vals = {
            "name": name,
            "state": "email",
            "usage": "ir_cron",
            "model_id": dict_val["model_id"],
        }
        action_server = self.env["ir.actions.server"].create(action_server_vals)
        automated_actions_vals = {
            "active": active,
            "action_server_id": action_server.id,
            "trigger": dict_val["trigger"],
            "filter_domain": dict_val["filter_domain"],
            "filter_pre_domain": dict_val["filter_pre_domain"],
            "trg_date_range": dict_val["time"],
            "trg_date_range_type": date_range_type,
            "template_id": template_id,
        }
        model_field = dict_val["model_field"]
        if model_field:
            automated_actions_vals.update(
                {
                    "trg_date_id": dict_val["model_field"].id,
                }
            )
        trigger_field = dict_val["trigger_fields"]
        if trigger_field:
            automated_actions_vals.update(
                {
                    "trigger_field_ids": dict_val["trigger_fields"].ids,
                }
            )
        automated_action = self.env["base.automation"].create(automated_actions_vals)
        vals.update({"automated_actions_id": automated_action.id})
        return super(PmsAutomatedMails, self).create(vals)

    def write(self, vals):
        result = super(PmsAutomatedMails, self).write(vals)
        is_create = False
        if (
            self.action in ("creation", "write", "cancel", "invoice")
            and self.moment == "before"
        ):
            raise UserError(_("The moment for this action cannot be 'Before'"))
        dict_val = self._prepare_automated_actions_id(
            self.action, self.time, self.moment, self.pms_property_ids, is_create
        )
        automated_actions_id = self.automated_actions_id
        action_server = automated_actions_id.action_server_id
        action_server_vals = {
            "name": self.name,
            "state": "email",
            "usage": "ir_cron",
            "model_id": dict_val["model_id"],
        }
        action_server.write(action_server_vals)
        automated_actions_vals = {
            "active": self.active,
            "action_server_id": action_server.id,
            "trigger": dict_val["trigger"],
            "filter_domain": dict_val["filter_domain"],
            "filter_pre_domain": dict_val["filter_pre_domain"],
            "trg_date_range": dict_val["time"],
            "trg_date_range_type": self.time_type,
            "template_id": self.template_id,
        }
        model_field = dict_val["model_field"]
        if model_field:
            automated_actions_vals.update(
                {
                    "trg_date_id": dict_val["model_field"].id,
                }
            )
        trigger_field = dict_val["trigger_fields"]
        if trigger_field:
            automated_actions_vals.update(
                {
                    "trigger_field_ids": dict_val["trigger_fields"].ids,
                }
            )
        automated_actions_id.write(automated_actions_vals)
        vals.update({"automated_actions_id": automated_actions_id.id})
        return result

    def unlink(self):
        automated_actions_id = self.automated_actions_id
        action_server = automated_actions_id.action_server_id
        automated_actions_id.unlink()
        action_server.unlink()
        return super(PmsAutomatedMails, self).unlink()

    @api.model
    def _get_auto_action_fields_in_creation_action(self, moment, time):
        model_field = False
        model_id = self.env["ir.model"].search([("model", "=", "pms.reservation")]).id
        if moment == "in_act":
            trigger = "on_create"
            time = 0
        else:
            trigger = "on_time"
            model_field = self.env["ir.model.fields"].search(
                [("model", "=", "pms.reservation"), ("name", "=", "create_date")]
            )
        result = {
            "model_id": model_id,
            "trigger": trigger,
            "model_field": model_field,
            "time": time,
        }
        return result

    @api.model
    def _get_auto_action_fields_in_write_or_cancel_action(self, moment, time):
        model_field = False
        model_id = self.env["ir.model"].search([("model", "=", "pms.reservation")]).id
        if moment == "in_act":
            trigger = "on_write"
            time = 0
        else:
            trigger = "on_time"
            model_field = self.env["ir.model.fields"].search(
                [("model", "=", "pms.reservation"), ("name", "=", "write_date")]
            )
        result = {
            "model_id": model_id,
            "trigger": trigger,
            "model_field": model_field,
            "time": time,
        }
        return result

    @api.model
    def _get_auto_action_fields_in_checkin_action(self, moment, time):
        model_id = self.env["ir.model"].search([("model", "=", "pms.reservation")]).id
        trigger = "on_time"
        model_field = self.env["ir.model.fields"].search(
            [("model", "=", "pms.reservation"), ("name", "=", "checkin")]
        )
        if moment == "before":
            time = time * (-1)
        if moment == "in_act":
            trigger = "on_write"
            time = 0
        result = {
            "model_id": model_id,
            "trigger": trigger,
            "model_field": model_field,
            "time": time,
        }
        return result

    @api.model
    def _get_auto_action_fields_in_checkout_action(self, moment, time):
        model_id = self.env["ir.model"].search([("model", "=", "pms.reservation")]).id
        trigger = "on_time"
        model_field = self.env["ir.model.fields"].search(
            [("model", "=", "pms.reservation"), ("name", "=", "checkout")]
        )
        if moment == "before":
            time = time * (-1)
        if moment == "in_act":
            trigger = "on_write"
            time = 0
        result = {
            "model_id": model_id,
            "trigger": trigger,
            "model_field": model_field,
            "time": time,
        }
        return result

    @api.model
    def _get_auto_action_fields_in_payment_action(self, moment, time):
        model_field = False
        model_id = (
            self.env["ir.model"]
            .search([("model", "=", "account.payment"), ("transient", "=", False)])
            .id
        )
        if moment == "in_act":
            trigger = "on_create"
            time = 0
        else:
            trigger = "on_time"
            model_field = self.env["ir.model.fields"].search(
                [("model", "=", "account.payment"), ("name", "=", "date")]
            )
            if moment == "before":
                time = time * (-1)
        result = {
            "model_id": model_id,
            "trigger": trigger,
            "model_field": model_field,
            "time": time,
        }
        return result

    @api.model
    def _get_auto_action_fields_in_invoice_action(self, moment, time):
        trigger = False
        model_id = self.env["ir.model"].search([("model", "=", "account.move")]).id
        if moment == "in_act":
            trigger = "on_create"
            time = 0
        result = {
            "model_id": model_id,
            "time": time,
            "trigger": trigger,
            "model_field": False,
        }
        return result

    def _prepare_automated_actions_id(
        self, action, time, moment, properties, is_create
    ):
        filter_domain = []
        filter_pre_domain = []
        trigger_fields = False
        dict_val = {}
        if action == "creation":
            dict_val = self._get_auto_action_fields_in_creation_action(moment, time)
        elif action == "write" or action == "cancel":
            dict_val = self._get_auto_action_fields_in_write_or_cancel_action(
                moment, time
            )
            if action == "cancel":
                filter_domain = [
                    ("state", "=", "cancelled"),
                ]
        elif action == "checkin":
            dict_val = self._get_auto_action_fields_in_checkin_action(moment, time)
            if moment == "in_act":
                trigger_fields = self.env["ir.model.fields"].search(
                    [("model", "=", "pms.reservation"), ("name", "=", "state")]
                )
                filter_pre_domain = [("state", "=", "confirm")]
                filter_domain = [
                    ("state", "=", "onboard"),
                ]
        elif action == "checkout":
            dict_val = self._get_auto_action_fields_in_checkout_action(moment, time)
            if moment == "in_act":
                trigger_fields = self.env["ir.model.fields"].search(
                    [("model", "=", "pms.reservation"), ("name", "=", "state")]
                )
                filter_pre_domain = [("state", "=", "onboard")]
                filter_domain = [
                    ("state", "=", "out"),
                ]
        elif action == "payment":
            dict_val = self._get_auto_action_fields_in_payment_action(moment, time)
        elif action == "invoice":
            dict_val = self._get_auto_action_fields_in_invoice_action(moment, time)
            filter_domain = [
                ("folio_ids", "!=", False),
            ]
        pms_property_ids = self._get_pms_property_ids(properties, is_create)
        if pms_property_ids:
            filter_domain.append(("pms_property_id", "in", pms_property_ids))
        result = {
            "trigger": dict_val["trigger"],
            "model_field": dict_val["model_field"],
            "trigger_fields": trigger_fields,
            "filter_pre_domain": filter_pre_domain,
            "filter_domain": filter_domain,
            "time": dict_val["time"],
            "model_id": dict_val["model_id"],
        }
        return result

    def _get_pms_property_ids(self, properties, is_create):
        pms_property_ids = []
        if is_create:
            pms_property_ids = properties[0][2]
        else:
            for pms_property in properties:
                pms_property_ids.append(pms_property.id)
        return pms_property_ids
