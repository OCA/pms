from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    downpayment_auto_enabled = fields.Boolean(
        string="Enable Auto Downpayment Invoicing",
        default=False,
        help="""If enabled, the daily cron will evaluate and run
        downpayment invoicing for this company according to the schedule below.""",
    )

    downpayment_auto_mode = fields.Selection(
        [
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly (last day of each quarter)"),
        ],
        string="Schedule Mode",
        default="monthly",
        help="Select how often the automation should run.",
    )

    downpayment_auto_weekday = fields.Selection(
        [
            ("mon", "Monday"),
            ("tue", "Tuesday"),
            ("wed", "Wednesday"),
            ("thu", "Thursday"),
            ("fri", "Friday"),
            ("sat", "Saturday"),
            ("sun", "Sunday"),
        ],
        string="Weekly Day",
        help="Required if mode is Weekly.",
    )

    downpayment_auto_monthly_marker = fields.Selection(
        [
            ("first", "First"),
            ("last", "Last"),
            ("penultimate", "Penultimate"),
            ("fixed", "Fixed Day (1..28)"),
        ],
        string="Monthly Marker",
        default="last",
        help="""
            Monthly trigger: first/last/penultimate day,
            or a fixed day (enter below).
        """,
    )

    downpayment_auto_monthly_day = fields.Integer(
        string="Monthly Day",
        help="If Monthly Marker is 'Fixed Day', set a day between 1 and 28.",
    )

    downpayment_auto_batch_size = fields.Integer(
        string="Batch Size", default=200, help="How many payments to process per batch."
    )
