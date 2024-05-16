from datetime import timedelta

from odoo import fields, models


class KlippaLog(models.Model):
    _name = "klippa.log"

    pms_property_id = fields.Many2one(
        string="PMS Property",
        help="PMS Property",
        comodel_name="pms.property",
        required=True,
    )
    request_id = fields.Text(
        string="Klippa Request ID",
        help="Request Klippa ID",
    )
    image_base64_front = fields.Text(
        string="Front Image",
        help="Front Image",
    )
    image_base64_back = fields.Text(
        string="Back Image",
        help="Back Image",
    )
    klippa_response = fields.Text(
        string="Klippa Response",
        help="Response",
    )
    klippa_status = fields.Char(
        string="Status",
        help="Status",
    )
    request_datetime = fields.Datetime(
        string="Request Date",
        help="Request Date",
    )
    response_datetime = fields.Datetime(
        string="Response Date",
        help="Response Date",
    )
    request_duration = fields.Float(
        string="Request Duration",
        help="Request Duration",
    )
    mapped_duration = fields.Float(
        string="Mapped Duration",
        help="Mapped Duration",
    )
    total_duration = fields.Float(
        string="Total Duration",
        help="Total Duration",
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
    request_url = fields.Char(
        string="Request URL",
        help="Request URL",
    )
    service_response = fields.Text(
        string="Resvice Response",
        help="Resvice Response",
    )
    final_status = fields.Char(
        string="Final Status",
        help="Final Status",
    )
    error = fields.Text(
        string="Error",
        help="Error",
    )

    def clean_log_data(self, offset=60):
        """Clean log data older than the offset.

        :param int offset: The number of days to keep the log data.

        """
        self.sudo().search(
            [
                ("final_status", "=", "success"),
                ("create_date", "<", fields.Datetime.now() - timedelta(days=offset)),
            ]
        ).unlink()
