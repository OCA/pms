from odoo import fields, models


class PmsLogInstitutionTravellerReport(models.Model):
    _name = "pms.log.institution.traveller.report"
    _description = "Report of daily sending files of travellers to institutions."

    date = fields.Datetime(
        string="Date and time",
        default=fields.Datetime.now,
    )
    error_sending_data = fields.Boolean(
        string="Error sending data",
        required=True,
    )
    txt_incidencies_from_institution = fields.Text(
        string="Detailed message",
    )
    file_incidencies_from_institution = fields.Binary(
        string="Detailed file",
    )
    txt_filename = fields.Text()
