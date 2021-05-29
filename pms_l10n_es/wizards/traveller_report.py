import base64
import datetime
import time
from datetime import date

import requests
from bs4 import BeautifulSoup as bs

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.modules.module import get_module_resource


class TravellerReport(models.TransientModel):
    _name = "traveller.report.wizard"
    _description = "Traveller Report"

    txt_filename = fields.Text()
    txt_binary = fields.Binary(string="File Download")
    txt_message = fields.Char(string="File Preview")

    def generate_file(self):

        # get the active property
        pms_property = self.env["pms.property"].search(
            [("id", "=", self.env.user.get_active_property_ids()[0])]
        )

        # build content
        content = self.generate_checkin_list(pms_property.id)

        if not pms_property.institution_property_id:
            raise ValidationError(
                _("The guest information sending settings is not property updated.")
            )
        elif not content:
            raise ValidationError(_("There is no guest information to send."))
        else:
            # file creation
            txt_binary = self.env["traveller.report.wizard"].create(
                {
                    "txt_filename": pms_property.institution_property_id + ".999",
                    "txt_binary": base64.b64encode(str.encode(content)),
                    "txt_message": content,
                }
            )
            return {
                "name": _("Traveller Report"),
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
        if self.env["pms.checkin.partner"].search_count(
            [
                ("state", "=", "onboard"),
                ("arrival", ">=", str(date.today()) + " 0:00:00"),
                ("arrival", "<=", str(date.today()) + " 23:59:59"),
            ]
        ):

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
                    content += line.lastname2.upper()
                content += "|" + line.firstname.upper() + "|"
                if line.gender == "female":
                    content += "F|"
                else:
                    content += "M|"
                content += line.birthdate_date.strftime("%Y%m%d") + "|"
                content += line.nationality_id.name.upper() + "|"
                content += line.arrival.strftime("%Y%m%d") + "\n"

            return content

    def send_file_gc(self, pms_property=False):
        url = "https://hospederias.guardiacivil.es/"
        login_route = "/hospederias/login.do"
        upload_file_route = "/hospederias/cargaFichero.do"
        logout_route = "/hospederias/logout.do"
        called_from_user = False
        if not pms_property:
            called_from_user = True
            # get the active property
            pms_property = self.env["pms.property"].search(
                [("id", "=", self.env.user.get_active_property_ids()[0])]
            )

        if not (
            pms_property
            and pms_property.institution_property_id
            and pms_property.institution_user
            and pms_property.institution_password
        ):
            raise ValidationError(
                _("The guest information sending settings is not complete.")
            )

        content = self.generate_checkin_list(pms_property.id)

        if content:
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 "
                "Build/MRA58N) AppleWebKit/537.36 (KHTML, like "
                "Gecko) Chrome/90.0.4430.93 Mobile Safari/537.36",
            }
            session = requests.session()
            login_payload = {
                "usuario": pms_property.institution_user,
                "pswd": pms_property.institution_password,
            }

            # login
            response_login = session.post(
                url + login_route,
                headers=headers,
                data=login_payload,
                verify=get_module_resource("pms_l10n_es", "static", "cert.pem"),
            )

            # check if authentication was successful / unsuccessful or the
            # resource cannot be accessed
            soup = bs(response_login.text, "html.parser")
            errors_login = soup.select("#txterror > ul > li")
            if errors_login:
                raise ValidationError(errors_login[0].text)
            else:
                login_correct = soup.select(".cabecera2")
                if not login_correct:
                    session.close()
                    raise ValidationError(_("Connection could not be established"))

            # build the file to send
            files = {"fichero": (pms_property.institution_user + ".999", content)}
            time.sleep(1)

            # send file
            response_file_sent = session.post(
                url + upload_file_route,
                data={"autoSeq": "on"},
                files=files,
                verify=get_module_resource("pms_l10n_es", "static", "cert.pem"),
            )

            time.sleep(1)
            # logout & close connection
            session.get(
                url + logout_route,
                headers=headers,
                verify=get_module_resource("pms_l10n_es", "static", "cert.pem"),
            )
            session.close()

            # check if the file send has been correct
            soup = bs(response_file_sent.text, "html.parser")
            errors = soup.select("#errores > tbody > tr")
            if errors:
                msg = "Errores en el fichero:\n"
                for e in errors:
                    msg += "Error en línea " + e.select("a")[0].text + ": "
                    msg += e.select("a")[2].text + "\n"
                raise ValidationError(msg)
            else:
                if called_from_user:
                    message = {
                        "type": "ir.actions.client",
                        "tag": "display_notification",
                        "params": {
                            "title": _("Sent succesfully!"),
                            "message": _("Successful file sending"),
                            "sticky": False,
                        },
                    }
                    return message

    @api.model
    def send_file_gc_async(self):
        for prop in self.env["pms.property"].search([]):
            self.with_delay().send_file_gc(prop)
