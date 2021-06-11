from odoo import fields, models


class PmsLogInstitutionTravellerReport(models.Model):
    _name = "pms.log.institution.traveller.report"
    _description = "Report of daily sending files of travellers to institutions."

    date = fields.Datetime(
        string="Date and time",
        default=fields.Datetime.now,
    )
    txtIncidenciesFromInstitution = fields.Text(
        string="Detailed message",
    )
    fileIncidenciesFromInstitution = fields.Binary(
        string="Detailed file",
    )
    txt_filename = fields.Text()
