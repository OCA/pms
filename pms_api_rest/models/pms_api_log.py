from odoo import _, api, fields, models


class PmsApiLog(models.Model):
    _name = "pms.api.log"

    pms_property_id = fields.Many2one(
        string="PMS Property",
        help="PMS Property",
        comodel_name="pms.property",
        default=lambda self: self.env.user.get_active_property_ids()[0],
    )
    client_id = fields.Many2one(
        string="Client",
        help="API Client",
        comodel_name="res.users",
    )
    request = fields.Text(
        string="Request",
        help="Request",
    )
    response = fields.Text(
        string="Response",
        help="Response",
    )
    status = fields.Selection(
        string="Status",
        help="Status",
        selection=[("success", "Success"), ("error", "Error")],
    )
    request_date = fields.Datetime(
        string="Request Date",
        help="Request Date",
    )
    response_date = fields.Datetime(
        string="Response Date",
        help="Response Date",
    )
    request_duration = fields.Float(
        string="Request Duration",
        help="Request Duration",
    )
    method = fields.Char(
        string="Method",
        help="Method",
    )
    endpoint = fields.Char(
        string="Endpoint",
        help="Endpoint",
    )
    request_size = fields.Integer(
        string="Request Size",
        help="Request Size",
    )
    response_size = fields.Integer(
        string="Response Size",
        help="Response Size",
    )
    request_headers = fields.Text(
        string="Request Headers",
        help="Request Headers",
    )
    response_headers = fields.Text(
        string="Response Headers",
        help="Response Headers",
    )
    request_url = fields.Char(
        string="Request URL",
        help="Request URL",
    )
    response_url = fields.Char(
        string="Response URL",
        help="Response URL",
    )
    model_id = fields.Many2one(
        string="Model",
        help="Model",
        comodel_name="ir.model",
    )

    def related_action_open_record(self):
        """Open a form view with the record(s) of the record log.

        For instance, for a job on a ``pms.folio``, it will open a
        ``pms.product`` form view with the product record(s) concerned by
        the job. If the job concerns more than one record, it opens them in a
        list.

        This is the default related action.

        """
        self.ensure_one()
        if "pms_api_log_id" in self.env[self.model_id.model]._fields:
            records = self.env[self.model_id.model].search(
                [("pms_api_log_id", "=", self.id)]
            )
        if not records:
            return None
        action = {
            "name": _("Related Record"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": records._name,
        }
        if len(records) == 1:
            action["res_id"] = records.id
        else:
            action.update(
                {
                    "name": _("Related Records"),
                    "view_mode": "tree,form",
                    "domain": [("id", "in", records.ids)],
                }
            )
        return action

    @api.model
    def create(self, vals):
        """
        set pms_api_log_id and origin_json in related records
        if record_ids id present in context
        """
        log_record = super().create(vals)
        if self.env.context.get("record_ids"):
            records = self.env[self.env.context.get("model")].browse(
                self.env.context.get("record_ids")
            )
            records.write(
                {
                    "pms_api_log_id": log_record.id,
                    "origin_json": log_record.request,
                }
            )
        return log_record
