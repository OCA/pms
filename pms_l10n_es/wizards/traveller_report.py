import base64
import datetime
import io
from datetime import date

import requests

from odoo import _, fields, models
from odoo.exceptions import ValidationError
from odoo.modules.module import get_module_resource


class TravellerReport(models.TransientModel):
    _name = "traveller.report.wizard"
    _description = "Traveller Report"

    txt_filename = fields.Char()
    txt_binary = fields.Binary()
    txt_message = fields.Char()

    def generate_file(self):

        # get the active property
        pms_property = self.env["pms.property"].search(
            [("id", "=", self.env.user.get_active_property_ids()[0])]
        )

        # build content
        content = self.generate_checkin_list(pms_property.id)

        # get next sequence
        sequence_num = self.env["ir.sequence"].next_by_code("traveller.report.wizard")

        # file creation
        txt_binary = self.env["traveller.report.wizard"].create(
            {
                "txt_filename": pms_property.institution_property_id
                + "."
                + sequence_num,
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

    def generate_checkin_list(self, property_id):

        # check if there's guests info pending to send
        if (
            self.env["pms.checkin.partner"].search_count(
                [
                    ("state", "=", "onboard"),
                    ("arrival", ">=", str(date.today()) + " 0:00:00"),
                    ("arrival", "<=", str(date.today()) + " 23:59:59"),
                ]
            )
            == 0
        ):
            raise ValidationError(_("There's no guests info to send"))
        else:

            # get the active property
            pms_property = self.env["pms.property"].search([("id", "=", property_id)])

            # check if the GC configuration info is properly set
            if not (
                pms_property.name
                and pms_property.institution_property_id
                and pms_property.institution_user
                and pms_property.institution_password
            ):
                raise ValidationError(
                    _("Check the GC configuration to send the guests info")
                )
            else:
                # get checkin partners info to send
                lines = self.env["pms.checkin.partner"].search(
                    [
                        ("state", "=", "onboard"),
                        ("arrival", ">=", str(date.today()) + " 0:00:00"),
                        ("arrival", "<=", str(date.today()) + " 23:59:59"),
                    ]
                )

                # build the property info record
                # 1 | property id | property name | date | nº of checkin partners

                content = (
                    "1|"
                    + pms_property.institution_property_id.upper()
                    + "|"
                    + pms_property.name.upper()
                    + "|"
                    + datetime.datetime.now().strftime("%Y%m%d|%H%M")
                    + "|"
                    + str(len(lines))
                    + "\n"
                )

            # build each checkin partner line's record
            # 2|DNI nº|Doc.number|doc.type|exp.date|lastname|lastname2|name|...
            # ...gender|birthdate|nation.|checkin

            for line in lines:
                content += "2"
                # [P|N|..]
                if line.document_type != "D":
                    content += "||" + line.document_number.upper() + "|"
                else:
                    content += "|" + line.document_number.upper() + "||"
                content += line.document_type + "|"
                content += line.document_expedition_date.strftime("%Y%m%d") + "|"
                content += line.lastname.upper() + "|"
                if line.lastname2:
                    content += line.lastname2.upper() + "|"
                content += line.firstname.upper() + "|"
                if line.gender == "female":
                    content += "F|"
                else:
                    content += "M|"
                content += line.birthdate_date.strftime("%Y%m%d") + "|"
                content += line.nationality_id.name.upper() + "|"
                content += line.arrival.strftime("%Y%m%d") + "\n"

            return content

    def send_file_gc(self):
        # get the active property
        pms_property = self.env["pms.property"].search(
            [("id", "=", self.env.user.get_active_property_ids()[0])]
        )

        # get next sequence to send
        sequence_num = self.env["ir.sequence"].next_by_code("traveller.report.wizard")

        # generate content to send
        f = io.StringIO(self.generate_checkin_list(pms_property.id))

        session = requests.Session()

        # send info to GC
        response = session.post(
            url="https://"
            + pms_property.institution_user
            + ":"
            + pms_property.institution_password
            + "@hospederias.guardiacivil.es/hospederias/servlet/"
            "ControlRecepcionFichero",
            files={
                "file": (
                    pms_property.institution_user + "." + sequence_num,
                    f,
                    "application/octet-stream",
                )
            },
            verify=get_module_resource("pms_l10n_es", "static", "cert.pem"),
        )
        # if the response is not ok raise validation error
        if response.content != b"CORRECTO\r\n":
            raise ValidationError(response.content.decode())
