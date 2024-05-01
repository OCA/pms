import base64
import datetime
import json
import logging
import re
import time

import requests
from bs4 import BeautifulSoup as bs
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import MissingError, ValidationError
from odoo.modules.module import get_module_resource

_logger = logging.getLogger(__name__)


class TravellerReport(models.TransientModel):
    _name = "traveller.report.wizard"
    _description = "Traveller Report"

    txt_filename = fields.Text()
    txt_binary = fields.Binary(string="File Download")
    txt_message = fields.Char(string="File Preview")
    date_target = fields.Date(
        string="Date", required=True, default=lambda self: fields.Date.today()
    )
    pms_property_id = fields.Many2one(
        comodel_name="pms.property",
        string="Property",
        required=True,
        default=lambda self: self.env.user.get_active_property_ids()[0],
    )

    def generate_file_from_user_action(self):
        pms_property = self.env["pms.property"].search(
            [("id", "=", self.pms_property_id.id)]
        )
        # check if there's institution settings properly established
        if (
            not pms_property
            or not pms_property.institution_property_id
            or not pms_property.institution_user
            or not pms_property.institution_password
        ):
            raise ValidationError(
                _("The guest information sending settings is not property updated.")
            )

        # build content
        content = self.generate_checkin_list(
            pms_property_id=pms_property.id,
            date_target=self.date_target,
        )

        if content:
            self.txt_filename = pms_property.institution_property_id + ".999"
            self.txt_binary = base64.b64encode(str.encode(content))
            self.txt_message = content

        return {
            "name": _("Traveller Report"),
            "res_id": self.id,
            "res_model": "traveller.report.wizard",
            "target": "new",
            "type": "ir.actions.act_window",
            "view_id": self.env.ref("pms_l10n_es.traveller_report_wizard").id,
            "view_mode": "form",
        }

    def generate_checkin_list(self, pms_property_id, date_target=False):
        regex = re.compile("[^a-zA-Z0-9]")

        # check if there's guests info pending to send
        if not date_target:
            date_target = fields.date.today()
        domain = [
            ("state", "in", ["onboard", "done"]),
            ("arrival", ">=", str(date_target) + " 0:00:00"),
            ("arrival", "<=", str(date_target) + " 23:59:59"),
            ("pms_property_id", "=", pms_property_id),
        ]
        pms_property = (
            self.env["pms.property"]
            .with_context(lang="es_ES")
            .search([("id", "=", pms_property_id)])
        )
        # get checkin partners info to send
        lines = self.env["pms.checkin.partner"].search(domain)
        # build the property info record
        # 1 | property id | property name | date | nº of checkin partners
        content = (
            "1|"
            + pms_property.institution_property_id.upper()
            + "|"
            + regex.sub(" ", pms_property.name.upper())
            + "|"
            + datetime.datetime.now().strftime("%Y%m%d|%H%M")
            + "|"
            + str(len(lines))
            + "\n"
        )
        # build each checkin partner line's record
        # 2|DNI nº|Doc.number|doc.type|exp.date|lastname|lastname2|name|...
        # ...gender|birthdate|nation.|checkin
        lines = lines.with_context(lang="es_ES")
        for line in lines:
            content += "2"
            # [P|N|..]
            if line.document_type.code not in ["D", "C"]:
                content += "||" + regex.sub("", line.document_number.upper()) + "|"
            else:
                content += "|" + regex.sub("", line.document_number.upper()) + "||"
            content += line.document_type.code + "|"
            content += line.document_expedition_date.strftime("%Y%m%d") + "|"
            content += regex.sub(" ", line.lastname.upper()) + "|"
            if line.lastname2:
                content += regex.sub(" ", line.lastname2.upper())
            content += "|" + regex.sub(" ", line.firstname.upper()) + "|"
            if line.gender == "female":
                content += "F|"
            else:
                content += "M|"
            content += line.birthdate_date.strftime("%Y%m%d") + "|"
            content += line.nationality_id.name.upper() + "|"
            content += line.arrival.strftime("%Y%m%d") + "\n"

        return content

    def send_file_gc(self, file_content, called_from_user, pms_property):
        try:
            _logger.info(
                "Sending file to Guardia Civil, Property %s, date: %s"
                % (pms_property.name, self.date_target)
            )
            url = "https://hospederias.guardiacivil.es/"
            login_route = "/hospederias/login.do"
            upload_file_route = "/hospederias/cargaFichero.do"
            logout_route = "/hospederias/logout.do"
            target_date = self.date_target or fields.date.today()
            if file_content:
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
                response_login = session.post(
                    url + login_route,
                    headers=headers,
                    data=login_payload,
                    verify=get_module_resource("pms_l10n_es", "static", "cert.pem"),
                )
                time.sleep(0.4)

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
                files = {
                    "fichero": (pms_property.institution_user + ".999", file_content)
                }

                # send file
                response_file_sent = session.post(
                    url + upload_file_route,
                    data={"autoSeq": "on"},
                    files=files,
                    verify=get_module_resource("pms_l10n_es", "static", "cert.pem"),
                )
                time.sleep(0.4)

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
                    return self.env["pms.log.institution.traveller.report"].create(
                        {
                            "error_sending_data": True,
                            "pms_property_id": pms_property.id,
                            "target_date": target_date,
                            "txt_message": _("Error in file sended"),
                            "txt_incidencies_from_institution": msg,
                        }
                    )
                else:
                    return self.env["pms.log.institution.traveller.report"].create(
                        {
                            "error_sending_data": False,
                            "pms_property_id": pms_property.id,
                            "target_date": target_date,
                            "txt_message": _("Successful file sending"),
                        }
                    )
        except Exception as e:
            return self.env["pms.log.institution.traveller.report"].create(
                {
                    "error_sending_data": True,
                    "pms_property_id": pms_property.id,
                    "target_date": target_date,
                    "txt_message": str(e),
                }
            )

    def send_file_pn(self, file_content, called_from_user, pms_property):
        try:
            base_url = "https://webpol.policia.es"
            headers = {
                "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 "
                "Build/MRA58N) AppleWebKit/537.36 (KHTML, like "
                "Gecko) Chrome/90.0.4430.93 Mobile Safari/537.36",
            }
            pre_login_route = "/e-hotel/login"
            login_route = "/e-hotel/execute_login"
            next_file_name_route = "/e-hotel/hospederia/ficheros/vista/envioFicheros"
            upload_file_route = "/e-hotel/hospederia/ficheros/subirFichero"

            pre_receipt_acknowledgment_route = (
                "/e-hotel/hospederia/generarInformeFichero"
            )

            post_receipt_acknowledgment_route2 = "/e-hotel/hospederia/pdfInformeFichero"
            logout_route = "/e-hotel/execute_logout"
            target_date = self.date_target or fields.date.today()
            session = requests.session()
            # retrieve token
            response_pre_login = session.post(
                base_url + pre_login_route,
                headers=headers,
                verify=False,
            )
            time.sleep(0.3)
            token = bs(response_pre_login.text, "html.parser").select(
                "input[name='_csrf']"
            )[0]["value"]

            if not token:
                raise MissingError(_("Could not get token login."))

            # do login
            session.post(
                base_url + login_route,
                headers=headers,
                data={
                    "username": pms_property.institution_user,
                    "password": pms_property.institution_password,
                    "_csrf": token,
                },
                verify=False,
            )
            time.sleep(0.3)
            headers["x-csrf-token"] = token
            # retrieve file name to send
            response_name_file_route = session.post(
                base_url + next_file_name_route,
                headers=headers,
                verify=False,
            )
            time.sleep(0.2)
            soup = bs(response_name_file_route.text, "html.parser")
            file_name = soup.select("#msjNombreFichero > b > u")[0].text

            if not file_name:
                raise MissingError(_("Could not get next file name to send."))

            # send file
            upload_result = session.post(
                base_url + upload_file_route,
                headers=headers,
                verify=False,
                data={
                    "jsonHiddenComunes": "",
                    "ficheroJ": "",
                    "_csrf": token,
                },
                files={"fichero": (file_name, file_content)},
            )
            if upload_result.status_code != 200:
                raise MissingError(_("Could not upload file."))

            time.sleep(0.2)
            # ask for receipt acknowledgment
            session.post(
                base_url + pre_receipt_acknowledgment_route,
                headers=headers,
                verify=False,
                data={
                    "jsonHiddenComunes": "",
                    "ficheroJ": json.loads(upload_result.content.decode("latin-1"))[
                        "ficheroJ"
                    ],
                    "_csrf": token,
                },
            )
            # get receipt acknowledgment
            response_post_ask_file2 = session.get(
                base_url + post_receipt_acknowledgment_route2,
            )
            time.sleep(0.5)
            log = self.env["pms.log.institution.traveller.report"].create(
                {
                    "pms_property_id": pms_property.id,
                    "target_date": target_date,
                    "error_sending_data": False,
                    "file_incidencies_from_institution": base64.b64encode(
                        response_post_ask_file2.content
                    ),
                    "txt_filename": file_name + ".pdf",
                }
            )
            # do logout
            session.post(
                base_url + logout_route,
                headers=headers,
                verify=False,
                data={"_csrf": token},
            )
            session.close()
            return log
        except Exception as e:
            return self.env["pms.log.institution.traveller.report"].create(
                {
                    "error_sending_data": True,
                    "txt_message": str(e),
                    "pms_property_id": pms_property.id,
                    "target_date": target_date,
                }
            )

    def send_file_institution(self, pms_property=False, offset=0, date_target=False):
        try:
            called_from_user = False
            if not pms_property:
                called_from_user = True
                pms_property = self.env["pms.property"].search(
                    [("id", "=", self.pms_property_id.id)]
                )
            if (
                not pms_property
                or not pms_property.institution_property_id
                or not pms_property.institution_user
                or not pms_property.institution_password
            ):
                raise ValidationError(
                    _("The guest information sending settings is not complete.")
                )
            date_target = self.date_target or False
            if not date_target:
                date_target = fields.Date.today()
            date_target = date_target - relativedelta(days=offset)
            file_content = self.generate_checkin_list(
                pms_property_id=pms_property.id,
                date_target=date_target,
            )
            if pms_property.institution == "policia_nacional":
                log = self.send_file_pn(file_content, called_from_user, pms_property)
            elif pms_property.institution == "guardia_civil":
                log = self.send_file_gc(file_content, called_from_user, pms_property)
            if log.error_sending_data:
                _logger.warning(
                    """
                    Error sending file, Property %s, date: %s, message: %s
                    """
                    % (pms_property.name, self.date_target, log.txt_message)
                )
                raise ValidationError(log.txt_incidencies_from_institution)
            _logger.info(
                """
                Successful file sending, sending confirmation mail,
                Property %s, date: %s" % (pms_property.name, self.date_target)
            """
            )
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
            else:
                template = self.env.ref(
                    "pms_l10n_es.notification_send_success_travel_report_email"
                )
                template.send_mail(log.id, force_send=True)
        except Exception as e:
            _logger.warning(
                """
                Error sending file, Property %s, date: %s, message: %s
                """
                % (pms_property.name, self.date_target, str(e))
            )
            if called_from_user:
                message = {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Error!"),
                        "message": _("Error sending file: %s" % e),
                        "sticky": False,
                    },
                }
                return message
            else:
                log = self.env["pms.log.institution.traveller.report"].create(
                    {
                        "error_sending_data": True,
                        "txt_incidencies_from_institution": str(e),
                        "pms_property_id": pms_property.id,
                        "target_date": date_target,
                    }
                )
                template = self.env.ref(
                    "pms_l10n_es.notification_send_error_travel_report_email"
                )
                template.send_mail(log.id, force_send=True)

    @api.model
    def send_file_institution_async(self, offset=0):
        for prop in self.env["pms.property"].search([]):
            if prop.institution:
                self.send_file_institution(pms_property=prop, offset=offset)
                time.sleep(0.5)
