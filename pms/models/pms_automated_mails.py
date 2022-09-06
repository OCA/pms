from odoo import fields, models


class PmsAutomatedMails(models.Model):
    _name = "pms.automated.mails"
    _description = "Automatic Mails"

    # TODO: Model to delete
    name = fields.Char(string="Name", help="Name of the automated mail.", required=True)
