import base64
import datetime
from datetime import date

import requests

from odoo import _, fields, models


class TravellerReport(models.TransientModel):
    _name = "traveller.report.wizard"
    _description = "Traveller Report"

    txt_filename = fields.Char()
    txt_binary = fields.Binary()
    txt_message = fields.Char()

    def generate_file(self):
        date_start = str(date.today()) + " 0:00:00"
        date_end = str(date.today()) + " 23:59:59"
        lines = self.env["pms.checkin.partner"].search(
            [
                ("state", "=", "onboard"),
                ("arrival", ">=", date_start),
                ("arrival", "<=", date_end),
            ]
        )
        if not lines:
            return
        pms_property = self.env["pms.property"].search(
            [("id", "=", self.env.user.get_active_property_ids()[0])]
        )
        if pms_property.police_number and pms_property.name:
            content = (
                "1|"
                + pms_property.police_number.upper()
                + "|"
                + pms_property.name.upper()
            )
            content += "|"
            content += datetime.datetime.now().strftime("%Y%m%d|%H%M")
            content += "|" + str(len(lines))
            for line in lines:
                if line.document_type == "D":
                    content += "\n2|" + line.document_number.upper() + "||"
                else:
                    content += "\n2||" + line.document_number.upper() + "|"
                content += line.document_type + "|"
                content += line.document_expedition_date.strftime("%Y%m%d") + "|"
                content += line.lastname.upper() + "|"
                if line.lastname2:
                    content += line.lastname2.upper()
                content += "|" + line.firstname.upper() + "|"
                if line.gender == "female":
                    content += "F|"
                else:
                    content += "M|"
                content += line.birthdate_date.strftime("%Y%m%d") + "|"
                # REVIEW: nationality_id must be nationality
                content += line.nationality_id.name.upper() + "|"
                content += line.arrival.strftime("%Y%m%d") + "|"
            sequence_num = self.env["ir.sequence"].next_by_code(
                "traveller.report.wizard"
            )
            txt_binary = self.env["traveller.report.wizard"].create(
                {
                    "txt_filename": pms_property.police_number + "." + sequence_num,
                    "txt_binary": base64.b64encode(str.encode(content)),
                    "txt_message": content,
                }
            )
            return {
                "name": _("Download File"),
                "res_id": txt_binary.id,
                "res_model": "traveller.report.wizard",
                "target": "new",
                "type": "ir.actions.act_window",
                "view_id": self.env.ref("pms_l10n_es.traveller_report_wizard").id,
                "view_mode": "form",
                "view_type": "form",
            }

    def send_guardia_civil_report(self):
        # TODO: Review this
        pms_property = self.env["pms.property"].search(
            [("id", "=", self.env.user.get_active_property_ids()[0])]
        )
        user = pms_property.police_user
        password = pms_property.police_pass
        if user and password:
            data = [self.txt_binary]
            requests.post(
                "https://usuario:password@hospederias.guardiacivil.es/"
                "hospederias/servlet/ControlRecepcionFichero",
                auth=(user, password),
                data=data,
            )
