from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

PMS_BUSINESS_MODELS = [
    ("pms.reservation"),
    ("pms.checkin.partner"),
    ("pms.service.line"),
    ("pms.folio"),
    ("account.move"),
    ("account.payment"),
]


class AdvancedFiltersWizard(models.TransientModel):
    _name = "pms.advanced.filters.wizard"
    _description = "Wizard for advanced filters"

    pms_model_id = fields.Many2one(
        string="Recipients Model",
        required=True,
        default=lambda self: self.env.ref("pms.model_pms_reservation").id,
        comodel_name="ir.model",
        domain=[("model", "in", PMS_BUSINESS_MODELS)],
        ondelete="cascade",
    )
    pms_model_name = fields.Char(
        string="Recipients Model Name",
        readonly=True,
        related="pms_model_id.model",
        related_sudo=True,
    )
    pms_domain = fields.Char(string="Domain")

    def action_filter(self):
        self.ensure_one()
        actions = {
            "pms.reservation": self.env.ref(
                "pms.open_pms_reservation_form_tree_all"
            ).read()[0],
            "pms.checkin.partner": self.env.ref("pms.action_checkin_partner").read()[0],
            "pms.service.line": self.env.ref("pms.action_service_line").read()[0],
            "pms.folio": self.env.ref("pms.open_pms_folio1_form_tree_all").read()[0],
            "account.move": self.env.ref("account.action_move_out_invoice_type").read()[
                0
            ],
            "account.payment": self.env.ref("account.action_account_payments").read()[
                0
            ],
        }
        domain = self.pms_domain
        if domain:
            domain = safe_eval(self.pms_domain)
            actions[self.pms_model_name]["domain"] = domain
            return actions[self.pms_model_name]
        else:
            raise UserError(_("You must add filters to perform the search"))
