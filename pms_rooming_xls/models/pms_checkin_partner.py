# Copyright 2009-2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re

from odoo import models


class PmsCheckinPartner(models.Model):
    _inherit = "pms.checkin.partner"

    def rooming_xls(self):
        module = __name__.split("addons.")[1].split(".")[0]
        report_name = "{}.rooming_export_xlsx".format(module)
        file_name = re.sub(
            r'[\\/*?:"<>|]', "", "Roomlist_" + "_".join(self.folio_id.mapped("name"))
        )
        report = {
            "type": "ir.actions.report",
            "report_type": "xlsx",
            "report_name": report_name,
            # model name will be used if no report_file passed via context
            "context": dict(self.env.context, report_file=file_name),
            # report_xlsx doesn't pass the context if the data dict is empty
            # cf. report_xlsx\static\src\js\report\qwebactionmanager.js
            # TODO: create PR on report_xlsx to fix this
            "data": {"dynamic_report": True},
        }
        return report
