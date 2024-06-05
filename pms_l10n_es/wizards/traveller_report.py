import base64
import csv
import datetime
import io
import json
import logging
import re
import time
import xml.etree.cElementTree as ET
import zipfile

import requests
from bs4 import BeautifulSoup as bs
from dateutil.relativedelta import relativedelta
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from odoo import _, api, fields, models
from odoo.exceptions import MissingError, ValidationError
from odoo.modules.module import get_module_resource

_logger = logging.getLogger(__name__)

CODE_SPAIN = "ES"
CODE_PASSPORT = "P"
CODE_DNI = "D"
CODE_NIE = "N"
# Disable insecure request warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def string_to_zip_to_base64(string_data):
    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr("data.xml", string_data.encode("utf-8"))
        zip_buffer.seek(0)
        zip_data = zip_buffer.read()
        zip_base64 = base64.b64encode(zip_data)
        return zip_base64.decode()
    except Exception as e:
        print(f"Error string to ZIP to Base64: {e}")
        return None


class TravellerReport(models.TransientModel):
    _name = "traveller.report.wizard"
    _description = "Traveller Report"

    txt_filename = fields.Text()
    txt_binary = fields.Binary(string="File Download")
    txt_message = fields.Char(
        string="File Preview",
        readonly=True,
        store=True,
        compute="_compute_txt_message",
    )
    date_target = fields.Date(
        string="Date", required=True, default=lambda self: fields.Date.today()
    )
    date_from = fields.Date(
        string="From",
        required=True,
        default=lambda self: fields.Date.today(),
    )
    date_to = fields.Date(
        string="To",
        required=True,
        default=lambda self: fields.Date.today() + relativedelta(days=1),
    )

    pms_property_id = fields.Many2one(
        comodel_name="pms.property",
        string="Property",
        required=True,
        default=lambda self: self.env.user.get_active_property_ids()[0],
    )

    is_ses = fields.Boolean(
        string="Is SES",
        readonly=True,
        compute="_compute_is_ses",
    )

    report_type = fields.Selection(
        string="Report Type",
        required=True,
        default="reservations",
        help="Report type (reservation/traveller report)",
        selection=[
            ("reservations", "Reservations Report"),
            ("travellers", "Travellers Report"),
        ],
    )

    @api.depends(
        "pms_property_id", "date_target", "date_from", "date_to", "report_type"
    )
    def _compute_txt_message(self):
        for record in self:
            record.txt_message = False

    @api.depends("pms_property_id.institution")
    def _compute_is_ses(self):
        for record in self:
            record.is_ses = record.pms_property_id.institution == "ses"

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
                _("The guest information sending settings is not property set up.")
            )

        content = False
        # build content
        if self.is_ses:
            if self.report_type == "travellers":
                content = self.generate_ses_travellers_list(
                    pms_property_id=pms_property.id,
                    date_target=self.date_target,
                )
            elif self.report_type == "reservations":
                content = self.generate_ses_reservation_list(
                    pms_property_id=pms_property.id,
                    date_from=self.date_from,
                    date_to=self.date_to,
                )
        else:
            content = self.generate_checkin_list(
                pms_property_id=pms_property.id,
                date_target=self.date_target,
            )

        if content:
            if self.is_ses:
                if self.report_type == "travellers":
                    self.txt_filename = (
                        pms_property.institution_property_id
                        + "-"
                        + self.date_target.strftime("%Y%m%d")
                    )
                else:
                    self.txt_filename = (
                        pms_property.institution_property_id
                        + "-"
                        + self.date_from.strftime("%Y%m%d")
                        + "-"
                        + self.date_to.strftime("%Y%m%d")
                    )
                self.txt_filename = self.txt_filename + ".xml"

            else:
                self.txt_filename = (
                    pms_property.institution_property_id
                    + "-"
                    + self.date_target.strftime("%Y%m%d")
                    + ".999"
                )

            self.txt_binary = base64.b64encode(str.encode(content))
            self.txt_message = content

        return {
            "name": _(
                "Travellers Report"
                if self.report_type == "travellers" or not self.is_ses
                else "Reservations Report"
            ),
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

    # SES RESERVATIONS
    def generate_ses_reservation_list(self, pms_property_id, date_from, date_to):
        reservation_ids = (
            self.env["pms.reservation"]
            .search(
                [
                    ("pms_property_id", "=", pms_property_id),
                    ("state", "!=", "cancel"),
                    ("reservation_type", "!=", "out"),
                    "|",
                    ("date_order", ">=", date_from),
                    ("date_order", "<=", date_to),
                ]
            )
            .mapped("id")
        )
        return self.generate_xml_reservations(reservation_ids)

    def generate_xml_reservation(self, solicitud, reservation_id):
        reservation = self.env["pms.reservation"].browse(reservation_id)

        if not reservation.pms_property_id.institution_property_id:
            raise ValidationError(
                _("The property does not have an institution property id.")
            )

        # SOLICITUD > COMUNICACION
        comunicacion = ET.SubElement(solicitud, "comunicacion")

        # SOLICITUD > COMUNICACION > ESTABLECIMIENTO
        establecimiento = ET.SubElement(comunicacion, "establecimiento")

        # SOLICITUD > COMUNICACION > ESTABLECIMIENTO > CODIGO
        ET.SubElement(
            establecimiento, "codigo"
        ).text = reservation.pms_property_id.institution_property_id

        # SOLICITUD > COMUNICACION > CONTRATO
        contrato = ET.SubElement(comunicacion, "contrato")

        # SOLICITUD > COMUNICACION > CONTRATO > REFERENCIA
        ET.SubElement(contrato, "referencia").text = reservation.name

        # SOLICITUD > COMUNICACION > CONTRATO > FECHA CONTRATO
        ET.SubElement(contrato, "fechaContrato").text = str(reservation.date_order)[
            0:10
        ]

        # SOLICITUD > COMUNICACION > CONTRATO > FECHA ENTRADA
        ET.SubElement(contrato, "fechaEntrada").text = (
            str(reservation.checkin)[0:10] + "T00:00:00"
        )

        # SOLICITUD > COMUNICACION > CONTRATO > FECHA SALIDA
        ET.SubElement(contrato, "fechaSalida").text = (
            str(reservation.checkout)[0:10] + "T00:00:00"
        )

        # SOLICITUD > COMUNICACION > CONTRATO > NUM PERSONAS
        ET.SubElement(contrato, "numPersonas").text = str(reservation.adults)

        # SOLICITUD > COMUNICACION > CONTRATO > PAGO
        pago = ET.SubElement(contrato, "pago")

        # SOLICITUD > COMUNICACION > CONTRATO > PAGO > TIPO PAGO
        # paymentw not cancelled or draft
        payments = reservation.folio_id.payment_ids.filtered(
            lambda x: x.state == "posted"
        )
        if payments:
            payment = payments[0]
            if payment.journal_id.type == "cash":
                ET.SubElement(pago, "tipoPago").text = "EFECT"
            else:
                ET.SubElement(pago, "tipoPago").text = "PLATF"
        else:
            ET.SubElement(pago, "tipoPago").text = "DESTI"

        # SOLICITUD > COMUNICACION > PERSONA
        persona = ET.SubElement(comunicacion, "persona")

        # SOLICITUD > COMUNICACION > PERSONA > ROL
        ET.SubElement(persona, "rol").text = "TI"

        # SOLICITUD > COMUNICACION > PERSONA > NOMBRE
        if reservation.partner_id.firstname:
            ET.SubElement(persona, "nombre").text = reservation.partner_id.firstname
        elif reservation.partner_name:
            ET.SubElement(persona, "nombre").text = reservation.partner_name.split(" ")[
                0
            ]
        else:
            raise ValidationError(_("The reservation does not have a name."))

        # SOLICITUD > COMUNICACION > PERSONA > APELLIDO1
        if reservation.partner_id.lastname:
            ET.SubElement(persona, "apellido1").text = reservation.partner_id.lastname
        elif reservation.partner_name and len(reservation.partner_name.split(" ")) > 1:
            ET.SubElement(persona, "apellido1").text = reservation.partner_name.split(
                " "
            )[1]
        else:
            ET.SubElement(persona, "apellido1").text = "No aplica"

        # SOLICITUD > COMUNICACION > PERSONA > TELEFONO
        if reservation.partner_id.mobile:
            ET.SubElement(persona, "telefono").text = reservation.partner_id.mobile
        elif reservation.partner_id.phone:
            ET.SubElement(persona, "telefono").text = reservation.partner_id.phone
            # SOLICITUD > COMUNICACION > PERSONA > EMAIL
        elif reservation.partner_id.email:
            ET.SubElement(persona, "correo").text = reservation.partner_id.email
        elif reservation.pms_property_id.email:
            ET.SubElement(persona, "correo").text = reservation.pms_property_id.email
        else:
            raise ValidationError(
                _(
                    "The reservation does not have a phone or email "
                    "or set a default property email."
                )
            )

    def generate_xml_reservations(self, reservation_ids):
        if not reservation_ids:
            raise ValidationError(_("Theres's no reservation to generate the XML"))

        # SOLICITUD
        solicitud = ET.Element("solicitud")
        for reservation_id in reservation_ids:
            ET.SubElement(
                solicitud,
                self.generate_xml_reservation(solicitud, reservation_id),
            )
        xml_str = ET.tostring(solicitud, encoding="unicode")

        xml_str = (
            '<ns2:peticion xmlns:ns2="http://www.neg.hospedajes.mir.es/altaReservaHospedaje">'
            + xml_str
            + "</ns2:peticion>"
        )
        return xml_str

    # SES RESERFVATIONS TRAVELLER REPORT
    def generate_ses_travellers_list(self, pms_property_id, date_target):
        reservation_ids = (
            self.env["pms.reservation"]
            .search(
                [
                    ("pms_property_id", "=", pms_property_id),
                    ("checkin", "=", date_target),
                ]
            )
            .mapped("id")
        )
        return self.generate_xml_reservations_travellers_report(reservation_ids)

    def generate_xml_reservation_travellers_report(self, solicitud, reservation_id):

        reservation = self.env["pms.reservation"].browse(reservation_id)

        # SOLICITUD -> COMUNICACION
        comunicacion = ET.SubElement(solicitud, "comunicacion")

        # SOLICITUD -> COMUNICACION -> CONTRATO
        contrato = ET.SubElement(comunicacion, "contrato")

        # SOLICITUD -> COMUNICACION -> CONTRATO -> REFERENCIA
        ET.SubElement(contrato, "referencia").text = reservation.name

        # SOLICITUD -> COMUNICACION -> CONTRATO -> FECHA CONTRATO
        ET.SubElement(contrato, "fechaContrato").text = str(reservation.date_order)[
            0:10
        ]

        # SOLICITUD -> COMUNICACION -> CONTRATO -> FECHA ENTRADA
        ET.SubElement(contrato, "fechaEntrada").text = (
            str(reservation.checkin)[0:10] + "T00:00:00"
        )

        # SOLICITUD -> COMUNICACION -> CONTRATO -> FECHA SALIDA
        ET.SubElement(contrato, "fechaSalida").text = (
            str(reservation.checkout)[0:10] + "T00:00:00"
        )

        # SOLICITUD -> COMUNICACION -> CONTRATO -> NUM PERSONAS
        ET.SubElement(contrato, "numPersonas").text = str(reservation.adults)

        # SOLICITUD -> COMUNICACION -> CONTRATO -> PAGO
        pago = ET.SubElement(contrato, "pago")

        # SOLICITUD > COMUNICACION > CONTRATO > PAGO > TIPO PAGO
        # paymentw not cancelled or draft
        payments = reservation.folio_id.payment_ids.filtered(
            lambda x: x.state == "posted"
        )
        if payments:
            payment = payments[0]
            if payment.journal_id.type == "cash":
                ET.SubElement(pago, "tipoPago").text = "EFECT"
            else:
                ET.SubElement(pago, "tipoPago").text = "PLATF"
        else:
            ET.SubElement(pago, "tipoPago").text = "DESTI"

        for checkin_partner in reservation.checkin_partner_ids.filtered(
            lambda x: x.state == "onboard"
        ):
            # SOLICITUD -> COMUNICACION -> PERSONA
            persona = ET.SubElement(comunicacion, "persona")

            # SOLICITUD -> COMUNICACION -> PERSONA -> ROL
            ET.SubElement(persona, "rol").text = (
                "TI"
                if checkin_partner.partner_id.id == reservation.partner_id.id
                else "VI"
            )

            # SOLICITUD -> COMUNICACION -> PERSONA -> NOMBRE
            if checkin_partner.firstname:
                ET.SubElement(persona, "nombre").text = checkin_partner.firstname
            else:
                raise ValidationError(_("The guest does not have a name."))

            # SOLICITUD -> COMUNICACION -> PERSONA -> APELLIDO1
            if checkin_partner.lastname:
                ET.SubElement(persona, "apellido1").text = checkin_partner.lastname
            else:
                raise ValidationError(_("The guest does not have a lastname."))

            # SOLICITUD -> COMUNICACION -> PERSONA -> TIPO DOCUMENTO
            if checkin_partner.document_type.code:
                if checkin_partner.document_type.code == CODE_DNI:
                    document_type = "NIF"
                elif checkin_partner.document_type.code == CODE_NIE:
                    document_type = "NIE"
                elif checkin_partner.document_type.code == CODE_PASSPORT:
                    document_type = "PAS"
                else:
                    document_type = "OTRO"
                ET.SubElement(persona, "tipoDocumento").text = document_type
            else:
                raise ValidationError(_("The guest does not have a document type."))

            # SOLICITUD -> COMUNICACION -> PERSONA -> SEGUNDO APELLIDO2
            if checkin_partner.document_type.code == CODE_DNI:
                if checkin_partner.partner_id.lastname2:
                    ET.SubElement(
                        persona, "apellido2"
                    ).text = checkin_partner.partner_id.lastname2
                else:
                    raise ValidationError(
                        _("The guest does not have a second lastname.")
                    )

            # SOLICITUD -> COMUNICACION -> PERSONA -> NUMERO DOCUMENTO
            if checkin_partner.document_number:
                ET.SubElement(
                    persona, "numeroDocumento"
                ).text = checkin_partner.document_number
            else:
                raise ValidationError(_("The guest does not have a document number."))

            # SOLICITUD -> COMUNICACION -> PERSONA -> NUMERO DE SOPORTE
            if (
                checkin_partner.document_type.code == CODE_DNI
                or checkin_partner.document_type.code == CODE_NIE
            ):
                if checkin_partner.support_number:
                    ET.SubElement(
                        persona, "soporteDocumento"
                    ).text = checkin_partner.support_number
                else:
                    raise ValidationError(
                        _("The guest does not have a support number.")
                    )

            # SOLICITUD -> COMUNICACION -> PERSONA -> FECHA NACIMIENTO
            if checkin_partner.birthdate_date:
                ET.SubElement(persona, "fechaNacimiento").text = str(
                    checkin_partner.birthdate_date
                )[0:10]
            else:
                raise ValidationError(_("The guest does not have a birthdate."))

            # SOLICITUD -> COMUNICACION -> PERSONA -> DIRECCION
            direccion = ET.SubElement(persona, "direccion")

            # SOLICITUD -> COMUNICACION -> PERSONA -> DIRECCION -> DIRECCION
            if checkin_partner.residence_street:
                ET.SubElement(
                    direccion, "direccion"
                ).text = checkin_partner.residence_street
            else:
                raise ValidationError(_("The guest does not have a street."))

            # SOLICITUD -> COMUNICACION -> PERSONA -> DIRECCION -> MUNICIPIO (INE) / LOCALIDAD
            if checkin_partner.residence_country_id.code == CODE_SPAIN:
                with open(
                    get_module_resource(
                        "pms_l10n_es",
                        "data/",
                        "pms.ine.zip.municipality.ine.relation.csv",
                    ),
                    "r",
                    newline="",
                ) as f:
                    lector = csv.reader(f)
                    for fila in lector:
                        if checkin_partner.residence_zip in fila[0]:
                            ET.SubElement(direccion, "codigoMunicipio").text = fila[1]
                            break
            else:
                if checkin_partner.residence_city:
                    # SOLICITUD -> COMUNICACION -> PERSONA -> DIRECCION -> LOCALIDAD
                    ET.SubElement(
                        direccion, "nombreMunicipio"
                    ).text = checkin_partner.residence_city
                else:
                    raise ValidationError(_("The guest does not have a city."))

            # SOLICITUD -> COMUNICACION -> PERSONA -> DIRECCION -> CP
            if checkin_partner.residence_zip:
                ET.SubElement(direccion, "cp").text = checkin_partner.residence_zip
            else:
                raise ValidationError(_("The guest does not have a zip code."))

            # SOLICITUD -> COMUNICACION -> PERSONA -> DIRECCION -> PAIS
            if checkin_partner.residence_country_id:
                ET.SubElement(
                    direccion, "pais"
                ).text = checkin_partner.residence_country_id.code_alpha3
            else:
                raise ValidationError(_("The guest does not have a country."))

            # SOLICITUD -> COMUNICACION -> PERSONA -> TELEFONO
            if checkin_partner.reservation_id.partner_id.mobile:
                ET.SubElement(persona, "telefono").text = checkin_partner.mobile
            elif checkin_partner.reservation_id.partner_id.phone:
                ET.SubElement(persona, "telefono").text = checkin_partner.phone
            # SOLICITUD -> COMUNICACION -> PERSONA -> EMAIL
            elif checkin_partner.reservation_id.partner_id.email:
                ET.SubElement(persona, "correo").text = checkin_partner.email
            elif checkin_partner.reservation_id.email:
                ET.SubElement(
                    persona, "correo"
                ).text = checkin_partner.reservation_id.email
            elif checkin_partner.reservation_id.pms_property_id.email:
                ET.SubElement(
                    persona, "correo"
                ).text = checkin_partner.reservation_id.pms_property_id.email
            else:
                raise ValidationError(
                    _("The guest does not have a contact method (mail or phone)")
                )

    def generate_xml_reservations_travellers_report(self, reservation_ids):
        if not reservation_ids:
            raise ValidationError(_("Theres's no reservation to generate the XML"))

        if (
            len(
                self.env["pms.reservation"]
                .browse(reservation_ids)
                .mapped("pms_property_id")
            )
            > 1
        ):
            raise ValidationError(_("The reservations must be from the same property."))
        if not any(
            state == "onboard"
            for state in self.env["pms.reservation"]
            .browse(reservation_ids)
            .mapped("checkin_partner_ids")
            .mapped("state")
        ):
            raise ValidationError(
                _("There are no guests to generate the travellers report.")
            )

        # SOLICITUD
        solicitud = ET.Element("solicitud")

        pms_property = (
            self.env["pms.reservation"].browse(reservation_ids[0]).pms_property_id
        )

        if not pms_property.institution_property_id:
            raise ValidationError(
                _("The property does not have an institution property id.")
            )

        # SOLICITUD -> CODIGO ESTABLECIMIENTO
        ET.SubElement(
            solicitud, "codigoEstablecimiento"
        ).text = pms_property.institution_property_id

        for reservation_id in reservation_ids:
            ET.SubElement(
                solicitud,
                self.generate_xml_reservation_travellers_report(
                    solicitud, reservation_id
                ),
            )
        xml_str = ET.tostring(solicitud, encoding="unicode")

        xml_str = (
            '<ns2:peticion xmlns:ns2="http://www.neg.hospedajes.mir.es/altaParteHospedaje">'
            + xml_str
            + "</ns2:peticion>"
        )
        return xml_str

    @api.model
    def send_comunication_ses(self, reservation_record, entity, operation_type):
        user = reservation_record.pms_property_id.institution_user
        password = reservation_record.pms_property_id.institution_password
        ses_url = reservation_record.pms_property_id.ses_url

        user_and_password_base64 = "Basic " + base64.b64encode(
            bytes(user + ":" + password, "utf-8")
        ).decode("utf-8")

        headers = {
            "Authorization": user_and_password_base64,
            "Content-Type": "text/xml; charset=utf-8",
        }
        lessor_id = reservation_record.pms_property_id.institution_lessor_id
        if entity == "RH":
            data = self.generate_xml_reservations([reservation_record.id])
        elif entity == "PV":
            data = self.generate_xml_reservation_travellers_report(
                [reservation_record.id]
            )
        data = string_to_zip_to_base64(data)

        payload = f"""
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                xmlns:com="http://www.soap.servicios.hospedajes.mir.es/comunicacion">
                <soapenv:Header/>
                <soapenv:Body>
                    <com:comunicacionRequest>
                        <peticion>
                            <cabecera>
                                <codigoArrendador>{lessor_id}</codigoArrendador>
                                <aplicacion>Roomdoo</aplicacion>
                                <tipoOperacion>{operation_type}</tipoOperacion>
                                <tipoComunicacion>{entity}</tipoComunicacion>
                            </cabecera>
                            <solicitud>{data}</solicitud>
                        </peticion>
                    </com:comunicacionRequest>
                </soapenv:Body>
            </soapenv:Envelope>
            """
        soap_response = requests.request(
            "POST", ses_url, headers=headers, data=payload, verify=False
        )
        root = ET.fromstring(soap_response.text)
        batch_number = root.find(".//lote").text
        return batch_number

    def send_pending_reservation_notifications(self):
        for record in self:
            for comunication in self.env["pms.ses.comunication"].search(
                [
                    ("state", "=", "to_send"),
                ]
            ):
                try:
                    comunication.comunication_id = self.send_comunication_ses(
                        comunication.reservation_id,
                        comunication.entity,
                        comunication.operation,
                    )
                    if comunication.operation == "A":
                        comunication.state = "to_process"
                    else:
                        comunication.state = "processed"
                except Exception as e:
                    print(e)
                    comunication.state = 'error_sending'

    def process_sent_comunications(self):
        for record in self:
            for comunication in self.env["pms.ses.comunication"].search(
                [
                    ("state", "=", "to_process"),
                    ("operation", "!=", "B"),
                ]
            ):
                pms_property = comunication.reservation_id.pms_property_id
                user = pms_property.institution_user
                password = pms_property.institution_password

                user_and_password_base64 = "Basic " + base64.b64encode(
                    bytes(user + ":" + password, "utf-8")
                ).decode("utf-8")

                headers = {
                    "Authorization": user_and_password_base64,
                    "Content-Type": "text/xml; charset=utf-8",
                }
                var_xml_get_batch = f"""
                    <con:lotes xmlns:con="http://www.neg.hospedajes.mir.es/consultarComunicacion">
                        <con:lote>{comunication.comunication_id}</con:lote>
                    </con:lotes>
                """
                data = string_to_zip_to_base64(var_xml_get_batch)
                payload = f"""
                    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                        xmlns:com="http://www.soap.servicios.hospedajes.mir.es/comunicacion">
                            <soapenv:Header/>
                            <soapenv:Body>
                                <com:comunicacionRequest>
                                    <peticion>
                                        <cabecera>
                                            <codigoArrendador>{pms_property.institution_property_id}</codigoArrendador>
                                            <aplicacion>Roomdoo</aplicacion>
                                            <tipoOperacion>C</tipoOperacion>
                                        </cabecera>
                                        <solicitud>{data}</solicitud>
                                    </peticion>
                                </com:comunicacionRequest>
                            </soapenv:Body>
                        </soapenv:Envelope>
                    """
                try:

                    soap_response = requests.request(
                        "POST",
                        pms_property.ses_url,
                        headers=headers,
                        data=payload,
                        verify=False,
                    )
                    root = ET.fromstring(soap_response.text)
                    error = root.find(".//error")
                    comunication.state = "processed"
                    comunication.processing_result = error or "ok"
                except Exception:
                    comunication.state = "error_processing"

