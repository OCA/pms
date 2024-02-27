from odoo import fields, models


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
