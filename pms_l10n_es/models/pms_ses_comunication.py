# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsSesComunication(models.Model):
    _name = "pms.ses.comunication"
    _description = "SES Comunication"
    reservation_id = fields.Many2one(
        string="Reservation",
        help="Reservation related to this comunication",
        index=True,
        required=True,
        comodel_name="pms.reservation",
    )
    comunication_id = fields.Char(
        string="Comunication ID",
        help="ID of the comunication",
        default=False,
    )
    operation = fields.Selection(
        string="Operation",
        help="Operation of the comunication",
        selection=[("A", "New comunication"), ("B", "Delete comunication")],
        required=True,
    )
    entity = fields.Selection(
        string="Entity",
        help="Entity of the comunication",
        selection=[("RH", "Reservation"), ("PV", "Traveller report")],
        required=True,
    )
    notification_time = fields.Datetime(
        string="Notification time",
        help="Date and time of the comunication",
    )
    processing_time = fields.Datetime(
        string="Processing time",
        help="Date and time of the comunication",
    )

    state = fields.Selection(
        string="State",
        help="State of the comunication",
        default="to_send",
        selection=[
            ("to_send", "Pending Notification"),
            ("error_sending", "Error Sending"),
            ("to_process", "Pending Processing"),
            ("error_processing", "Error Processing"),
            ("processed", "Processed"),
            ("error", "Error"),
        ],
    )
    processing_result = fields.Text(
        string="Processing Result",
        help="Notification processing result",
    )
    xml_content_sent = fields.Text(
        string="XML Content Sent",
        help="XML content of the comunication",
    )
    soap_content_sent = fields.Text(
        string="SOAP Content Sent",
        help="SOAP content of the comunication",
    )
    xml_content_process = fields.Text(
        string="XML Content Process",
        help="XML content of the comunication",
    )
    soap_content_process = fields.Text(
        string="SOAP Content Process",
        help="SOAP content of the comunication",
    )
