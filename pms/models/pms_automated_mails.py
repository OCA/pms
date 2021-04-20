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

    def _prepare_automated_actions_id(
        self, action, time, moment, properties, is_create
    ):
        trigger = False
        model_field = False
        model_id = False
        filter_domain = []
        today = fields.Date.today()
        # action: create reservation
        if action == "creation":
            model_id = (
                self.env["ir.model"].search([("model", "=", "pms.reservation")]).id
            )
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
            model_id = (
                self.env["ir.model"].search([("model", "=", "pms.reservation")]).id
            )
            if moment == "in_act":
                trigger = "on_write"
                time = 0
            else:
                trigger = "on_time"
                model_field = self.env["ir.model.fields"].search(
                    [("model", "=", "pms.reservation"), ("name", "=", "write_date")]
                )
            if action == "cancel":
                filter_domain = [
                    ("state", "=", "cancelled"),
                ]
        # action: checkin
        if action == "checkin":
            model_id = (
                self.env["ir.model"].search([("model", "=", "pms.reservation")]).id
            )
            trigger = "on_time"
            model_field = self.env["ir.model.fields"].search(
                [("model", "=", "pms.reservation"), ("name", "=", "checkin")]
            )
            if moment == "in_act":
                time = 0
                filter_domain = [
                    ("checkin", "=", str(today)),
                ]
            elif moment == "before":
                time = time * (-1)
        # action: checkout
        if action == "checkout":
            model_id = (
                self.env["ir.model"].search([("model", "=", "pms.reservation")]).id
            )
            trigger = "on_time"
            model_field = self.env["ir.model.fields"].search(
                [("model", "=", "pms.reservation"), ("name", "=", "checkout")]
            )
            if moment == "in_act":
                time = 0
                filter_domain = [
                    ("checkout", "=", str(today)),
                ]
            elif moment == "before":
                time = time * (-1)
        # action: payments
        if action == "payment":
            model_id = (
                self.env["ir.model"]
                .search([("model", "=", "account.payment"), ("transient", "=", False)])
                .id
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
        # TODO: create automated action when the act is 'invoice'
        # action: invoices
        # if action == "invoice":
        #     model_id = self.env["ir.model"].search(
        #       [("model", "=", "account.move")]
        #     ).id
        #     filter_domain = [
        #         ("folio_ids", "!=", False),
        #     ]
        #     if moment == "in_act":
        #         trigger = "on_create"
        #         time = 0
        pms_property_ids = self._get_pms_property_ids(properties, is_create)
        if pms_property_ids:
            filter_domain.append(("pms_property_id", "in", pms_property_ids))
        result = {
            "trigger": trigger,
            "model_field": model_field,
            "filter_domain": filter_domain,
            "time": time,
            "model_id": model_id,
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
