from datetime import timedelta

from odoo import _, fields, models


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
    request_type = fields.Selection(
        string="Request Type",
        help="Request Type",
        selection=[
            ("folios", "Folios"),
            ("availability", "Availability"),
            ("restrictions", "Restrictions rules"),
            ("prices", "Prices"),
        ],
    )
    target_date_from = fields.Date(
        string="Target Date From",
        help="Target Date From",
    )
    target_date_to = fields.Date(
        string="Target Date To",
        help="Target Date To",
    )
    folio_ids = fields.Many2many(
        string="Folios",
        help="Folios",
        comodel_name="pms.folio",
        relation="pms_folio_pms_api_log_rel",
        column1="pms_api_log_ids",
        column2="folio_ids",
    )
    room_type_ids = fields.Many2many(
        string="Room Types",
        help="Room Types",
        comodel_name="pms.room.type",
        relation="pms_room_type_pms_api_log_rel",
        column1="pms_api_log_ids",
        column2="room_type_ids",
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
        records = self.folio_ids
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

    def clean_log_data(self, offset=60):
        """Clean log data older than the offset.

        :param int offset: The number of days to keep the log data.

        """
        self.sudo().search(
            [
                ("status", "=", "success"),
                ("create_date", "<", fields.Datetime.now() - timedelta(days=offset)),
            ]
        ).unlink()
