from datetime import timedelta

from odoo import fields, models


class KlippaLog(models.Model):
    _name = "klippa.log"
    _description = "Klippa Log"
    _order = "id desc"

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
        help="Response",
    )
    klippa_status = fields.Char(
        help="Klippa Status",
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
        help="Request Duration",
    )
    mapped_duration = fields.Float(
        help="Mapped Duration",
    )
    total_duration = fields.Float(
        help="Total Duration",
    )
    endpoint = fields.Char(
        help="Endpoint",
    )
    request_size = fields.Integer(
        help="Request Size",
    )
    response_size = fields.Integer(
        help="Response Size",
    )
    request_headers = fields.Text(
        help="Request Headers",
    )
    request_url = fields.Char(
        help="Request URL",
    )
    service_response = fields.Text(
        help="Resvice Response",
    )
    final_status = fields.Char(
        help="Final Status",
    )
    error = fields.Text(
        help="Error",
    )
    nominatim_status = fields.Char(
        help="Nominatim Status",
    )
    nominatim_response = fields.Text(
        help="Nominatim Response",
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
