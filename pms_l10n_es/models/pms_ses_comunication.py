# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class PmsSesComunication(models.Model):
    _name = "pms.ses.comunication"
    _description = "SES Comunication"
    reservation_id = fields.Many2one(
        string="Reservation Reference",
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
    date_time = fields.Datetime(
        string="Date and Time",
        help="Date and time of the comunication",
        default=fields.Datetime.now(),
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
