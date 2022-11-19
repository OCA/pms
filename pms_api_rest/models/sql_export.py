from odoo import _, models
from odoo.exceptions import UserError


class SqlExport(models.Model):
    _inherit = "sql.export"

    def unlink(self):
        if (
            self.env.ref("pms_api_rest.sql_export_services") in self
            or self.env.ref("pms_api_rest.sql_export_departures") in self
            or self.env.ref("pms_api_rest.sql_export_arrivals") in self
        ):
            raise UserError(_("You can not delete PMS SQL query"))
        return super().unlink()
