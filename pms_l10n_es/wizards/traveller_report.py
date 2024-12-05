import base64
import csv
import datetime
import io
import json
import logging
import re
import time
import traceback
import xml.etree.cElementTree as ET
import zipfile

import requests
from bs4 import BeautifulSoup as bs
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import MissingError, ValidationError
from odoo.modules.module import get_module_resource

_logger = logging.getLogger(__name__)

CODE_SPAIN = "ES"
CODE_PASSPORT = "P"
CODE_DNI = "D"
CODE_NIE = "N"

REQUEST_CODE_OK = "0"
XML_OK = "1"
XML_PROCESSING = "4"
XML_PENDING = "5"

CREATE_OPERATION_CODE = "A"
DELETE_OPERATION_CODE = "B"


# Disable insecure request warnings
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def replace_multiple_spaces(text: str) -> str:
    # Replace 2 or more consecutive spaces with a single space
    return re.sub(r"\s{2,}", " ", text)


def clean_string_only_letters(string):
    clean_string = re.sub(r"[^a-zA-Z\s]", "", string).upper()
    clean_string = " ".join(clean_string.split())
    return clean_string


def clean_string_only_numbers_and_letters(string):
    clean_string = re.sub(r"[^a-zA-Z0-9\s]", "", string).upper()
    clean_string = " ".join(clean_string.split())
    return clean_string


def _string_to_zip_to_base64(string_data):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("data.xml", string_data.encode("utf-8"))
    zip_buffer.seek(0)
    zip_data = zip_buffer.read()
    zip_base64 = base64.b64encode(zip_data)
    return zip_base64.decode()


def _ses_xml_payment_elements(contrato, reservation):
    pago = ET.SubElement(contrato, "pago")
    payments = reservation.folio_id.payment_ids.filtered(lambda x: x.state == "posted")
    tipo_pago = "DESTI"
    if payments:
        payment = payments[0]
        tipo_pago = "EFECT" if payment.journal_id.type == "cash" else "PLATF"
    ET.SubElement(pago, "tipoPago").text = tipo_pago


def _ses_xml_contract_elements(comunicacion, reservation, people=False):
    contrato = ET.SubElement(comunicacion, "contrato")
    ET.SubElement(contrato, "referencia").text = reservation.name
    ET.SubElement(contrato, "fechaContrato").text = str(reservation.date_order)[:10]
    ET.SubElement(
        contrato, "fechaEntrada"
    ).text = f"{str(reservation.checkin)[:10]}T00:00:00"
    ET.SubElement(
        contrato, "fechaSalida"
    ).text = f"{str(reservation.checkout)[:10]}T00:00:00"
    if people:
        ET.SubElement(contrato, "numPersonas").text = str(people)
    else:
        ET.SubElement(contrato, "numPersonas").text = str(reservation.adults)
    _ses_xml_payment_elements(contrato, reservation)


def _ses_xml_text_element_and_validate(parent, tag, text, error_message):
    if text:
        ET.SubElement(parent, tag).text = text
    else:
        raise ValidationError(error_message)


def _ses_xml_map_document_type(code):
    if code == CODE_DNI:
        return "NIF"
    elif code == CODE_NIE:
        return "NIE"
    elif code == CODE_PASSPORT:
        return "PAS"
    else:
        return "OTRO"


def _ses_xml_person_names_elements(persona, reservation, checkin_partner):
    if reservation:
        ses_firstname = False
        if reservation.partner_id.firstname:
            ses_firstname = clean_string_only_letters(reservation.partner_id.firstname)[
                :50
            ]
        elif reservation.partner_name:
            ses_firstname = clean_string_only_letters(
                replace_multiple_spaces(reservation.partner_name)
            ).split(" ")[0][:50]
        _ses_xml_text_element_and_validate(
            persona,
            "nombre",
            ses_firstname,
            _("The reservation does not have a name."),
        )

        if reservation.partner_id.lastname:
            ses_lastname = clean_string_only_letters(reservation.partner_id.lastname)[
                :50
            ]
        elif (
            reservation.partner_name
            and len(replace_multiple_spaces(reservation.partner_name).split(" ")) > 1
        ):
            ses_lastname = clean_string_only_letters(
                replace_multiple_spaces(reservation.partner_name)
            ).split(" ")[1][:50]
        else:
            ses_lastname = "No aplica"
        ET.SubElement(persona, "apellido1").text = ses_lastname

    elif checkin_partner:
        _ses_xml_text_element_and_validate(
            persona,
            "nombre",
            clean_string_only_letters(checkin_partner.firstname)[:50],
            _("The guest does not have a name."),
        )
        _ses_xml_text_element_and_validate(
            persona,
            "apellido1",
            clean_string_only_letters(checkin_partner.lastname)[:50],
            _("The guest does not have a lastname."),
        )

        if checkin_partner.document_type.code == CODE_DNI:
            _ses_xml_text_element_and_validate(
                persona,
                "apellido2",
                clean_string_only_letters(checkin_partner.partner_id.lastname2)[:50],
                _("The guest does not have a second lastname."),
            )


def _ses_xml_person_personal_info_elements(persona, checkin_partner):
    ET.SubElement(persona, "rol").text = "VI"

    _ses_xml_person_names_elements(
        persona, reservation=False, checkin_partner=checkin_partner
    )

    if checkin_partner.document_type.code:
        document_type = _ses_xml_map_document_type(checkin_partner.document_type.code)
        ET.SubElement(persona, "tipoDocumento").text = document_type
    else:
        raise ValidationError(_("The guest does not have a document type."))

    _ses_xml_text_element_and_validate(
        persona,
        "numeroDocumento",
        checkin_partner.document_number,
        _("The guest does not have a document number."),
    )

    if checkin_partner.document_type.code in [CODE_DNI, CODE_NIE]:
        _ses_xml_text_element_and_validate(
            persona,
            "soporteDocumento",
            checkin_partner.support_number,
            _("The guest does not have a support number."),
        )
    _ses_xml_text_element_and_validate(
        persona,
        "fechaNacimiento",
        str(checkin_partner.birthdate_date)[:10],
        _("The guest does not have a birthdate."),
    )


def _ses_xml_municipality_code(residence_zip, pms_property):
    with open(
        get_module_resource(
            "pms_l10n_es", "static/src/", "pms.ine.zip.municipality.ine.relation.csv"
        ),
        "r",
        newline="",
    ) as f:
        lector = csv.reader(f)
        for fila in lector:
            if residence_zip in fila[0]:
                return fila[1][:5]
        # REVIEW: If the zip code is not found,
        # use provisory pms_property zip code
        property_zip = pms_property.zip
        if property_zip:
            return property_zip[:5]
    raise ValidationError(_("The guest does not have a valid zip code."))


def _ses_xml_person_address_elements(persona, checkin_partner):
    direccion = ET.SubElement(persona, "direccion")
    _ses_xml_text_element_and_validate(
        direccion,
        "direccion",
        checkin_partner.residence_street,
        _("The guest does not have a street."),
    )

    if checkin_partner.residence_country_id.code == CODE_SPAIN:
        municipio_code = _ses_xml_municipality_code(
            residence_zip=checkin_partner.residence_zip,
            pms_property=checkin_partner.reservation_id.pms_property_id,
        )
        if municipio_code:
            ET.SubElement(direccion, "codigoMunicipio").text = municipio_code
    else:
        _ses_xml_text_element_and_validate(
            direccion,
            "nombreMunicipio",
            checkin_partner.residence_city,
            _("The guest does not have a city."),
        )

    _ses_xml_text_element_and_validate(
        direccion,
        "codigoPostal",
        checkin_partner.residence_zip,
        _("The guest does not have a zip code."),
    )
    _ses_xml_text_element_and_validate(
        direccion,
        "pais",
        checkin_partner.residence_country_id.code_alpha3,
        _("The guest does not have a country."),
    )


def _ses_xml_person_contact_elements(persona, reservation, checkin_partner=False):
    partner = reservation.partner_id
    contact_methods = []
    if checkin_partner:
        contact_methods.extend(
            [
                checkin_partner.mobile,
                checkin_partner.phone,
                checkin_partner.email,
            ]
        )
    contact_methods.extend(
        [
            partner.mobile,
            partner.phone,
            partner.email,
            reservation.email,
            reservation.pms_property_id.partner_id.email,
            reservation.pms_property_id.partner_id.phone,
        ]
    )

    for contact in contact_methods:
        if contact:
            if "@" in contact:
                tag = "correo"
                contact = contact[0:50]
            else:
                tag = "telefono"
                contact = contact[0:20]
            ET.SubElement(persona, tag).text = contact
            break
    else:
        raise ValidationError(
            _(
                "The guest/reservation partner and property does not "
                "have a contact method (mail or phone)"
            )
        )


def _ses_xml_person_elements(comunicacion, checkin_partner):
    persona = ET.SubElement(comunicacion, "persona")
    _ses_xml_person_personal_info_elements(persona, checkin_partner)
    _ses_xml_person_address_elements(persona, checkin_partner)
    _ses_xml_person_contact_elements(
        persona, checkin_partner.reservation_id, checkin_partner
    )


def _get_auth_headers(communication):
    user = communication.reservation_id.pms_property_id.institution_user
    password = communication.reservation_id.pms_property_id.institution_password

    user_and_password_base64 = "Basic " + base64.b64encode(
        bytes(user + ":" + password, "utf-8")
    ).decode("utf-8")

    return {
        "Authorization": user_and_password_base64,
        "Content-Type": "text/xml; charset=utf-8",
    }


def _generate_payload(lessor_id, operation, entity, data):
    return f"""
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
            xmlns:com="http://www.soap.servicios.hospedajes.mir.es/comunicacion">
            <soapenv:Header/>
            <soapenv:Body>
                <com:comunicacionRequest>
                    <peticion>
                        <cabecera>
                            <codigoArrendador>{lessor_id}</codigoArrendador>
                            <aplicacion>Roomdoo</aplicacion>
                            <tipoOperacion>{operation}</tipoOperacion>
                            {
    '<tipoComunicacion>'+entity+'</tipoComunicacion>' if entity else ''
    }
                        </cabecera>
                        <solicitud>{data}</solicitud>
                    </peticion>
                </com:comunicacionRequest>
            </soapenv:Body>
        </soapenv:Envelope>
    """


def _handle_request_exception(communication, e):
    if isinstance(e, requests.exceptions.RequestException):
        if isinstance(e, requests.exceptions.ConnectionError):
            if communication.state == "to_send":
                communication.sending_result = (
                    f"Cannot establish the connection. ({e.args})"
                )
            else:
                communication.processing_result = (
                    f"Cannot establish the connection. ({e.args})"
                )
        elif isinstance(e, requests.exceptions.Timeout):
            if communication.state == "to_send":
                communication.sending_result = (
                    f"The request took too long to complete. ({e.args})"
                )
            else:
                communication.processing_result = (
                    f"The request took too long to complete. ({e.args})"
                )
        else:
            if communication.state == "to_send":
                communication.sending_result = (
                    f"Request error: {traceback.format_exc()}"
                )
            else:
                communication.processing_result = (
                    f"Request error: {traceback.format_exc()}"
                )
    else:
        communication.sending_result = f"Unexpected error: {traceback.format_exc()}"


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
        called_from_user = False
        log = False
        try:
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
        _ses_xml_contract_elements(comunicacion, reservation)

        # SOLICITUD > COMUNICACION > PERSONA
        persona = ET.SubElement(comunicacion, "persona")

        # SOLICITUD > COMUNICACION > PERSONA > ROL
        ET.SubElement(persona, "rol").text = "TI"

        # SOLICITUD > COMUNICACION > PERSONA > NOMBRE
        _ses_xml_person_names_elements(persona, reservation, checkin_partner=None)
        _ses_xml_person_contact_elements(persona, reservation)

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

    # SES RESERVATIONS TRAVELLER REPORT
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

    def generate_xml_reservation_travellers_report(
        self, solicitud, reservation_id, people=False
    ):
        reservation = self.env["pms.reservation"].browse(reservation_id)
        comunicacion = ET.SubElement(solicitud, "comunicacion")
        _ses_xml_contract_elements(comunicacion, reservation, people)
        for checkin_partner in reservation.checkin_partner_ids.filtered(
            lambda x: x.state in ["onboard", "done"]
        ):
            _ses_xml_person_elements(comunicacion, checkin_partner)

    def generate_xml_reservations_travellers_report(
        self, reservation_ids, ignore_some_not_onboard=False
    ):
        if not reservation_ids:
            raise ValidationError(_("Theres's no reservation to generate the XML"))
        elif (
            len(
                self.env["pms.reservation"]
                .browse(reservation_ids)
                .mapped("pms_property_id")
            )
            > 1
        ):
            raise ValidationError(_("The reservations must be from the same property."))
        elif all(
            state not in ["onboard", "done"]
            for state in self.env["pms.reservation"]
            .browse(reservation_ids)
            .mapped("checkin_partner_ids")
            .mapped("state")
        ):
            raise ValidationError(_("There are no guests onboard."))
        elif not ignore_some_not_onboard and any(
            state not in ["onboard", "done"]
            for state in self.env["pms.reservation"]
            .browse(reservation_ids)
            .mapped("checkin_partner_ids")
            .mapped("state")
        ):
            raise ValidationError(_("There are some guests not onboard."))
        else:
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
                if ignore_some_not_onboard:
                    num_people_on_board = len(
                        self.env["pms.reservation"]
                        .browse(reservation_id)
                        .checkin_partner_ids.filtered(
                            lambda x: x.state in ["onboard", "done"]
                        )
                    )
                    ET.SubElement(
                        solicitud,
                        self.generate_xml_reservation_travellers_report(
                            solicitud, reservation_id, people=num_people_on_board
                        ),
                    )
                else:
                    ET.SubElement(
                        solicitud,
                        self.generate_xml_reservation_travellers_report(
                            solicitud,
                            reservation_id,
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
    def ses_send_communications(self, entity, pms_ses_communication_id=False):
        domain = [
            ("state", "=", "to_send"),
            ("entity", "=", entity),
        ]
        if pms_ses_communication_id:
            domain.append(("id", "=", pms_ses_communication_id))
        for communication in self.env["pms.ses.communication"].search(domain):
            data = False
            try:
                if communication.operation == DELETE_OPERATION_CODE:
                    communication_to_cancel = self.env["pms.ses.communication"].search(
                        [
                            ("reservation_id", "=", communication.reservation_id.id),
                            ("state", "!=", "to_send"),
                            ("entity", "=", communication.entity),
                            ("operation", "=", CREATE_OPERATION_CODE),
                        ],
                        order="id desc",
                        limit=1,
                    )
                    data = (
                        "<anul:comunicaciones "
                        'xmlns:anul="http://www.neg.hospedajes.mir.es/anularComunicacion">'
                        + "<anul:codigoComunicacion>"
                        + communication_to_cancel.communication_id
                        + "</anul:codigoComunicacion>"
                        + "</anul:comunicaciones>"
                    )
                elif communication.operation == CREATE_OPERATION_CODE:
                    if communication.entity == "RH":
                        data = self.generate_xml_reservations(
                            [communication.reservation_id.id]
                        )
                    elif communication.entity == "PV":
                        data = self.generate_xml_reservations_travellers_report(
                            [communication.reservation_id.id]
                        )
                communication.communication_xml = data
                data = _string_to_zip_to_base64(data)
                payload = _generate_payload(
                    communication.reservation_id.pms_property_id.institution_lessor_id,
                    communication.operation,
                    communication.entity,
                    data,
                )
                communication.communication_soap = payload
                communication.communication_time = fields.Datetime.now()

                soap_response = requests.request(
                    "POST",
                    communication.reservation_id.pms_property_id.ses_url,
                    headers=_get_auth_headers(communication),
                    data=payload,
                    verify=get_module_resource("pms_l10n_es", "static", "cert.pem"),
                )
                soap_response.raise_for_status()

                root = ET.fromstring(soap_response.text)
                communication.sending_result = root.find(".//descripcion").text
                communication.response_communication_soap = soap_response.text
                result_code = root.find(".//codigo").text
                if result_code == REQUEST_CODE_OK:
                    communication.batch_id = root.find(".//lote").text

                    communication.state = "to_process"
                else:
                    communication.state = "error_sending"

            except requests.exceptions.HTTPError as http_err:
                _handle_request_exception(communication, http_err)
            except requests.exceptions.RequestException as e:
                _handle_request_exception(communication, e)
            except Exception as e:
                _handle_request_exception(communication, e)

    @api.model
    def ses_send_incomplete_traveller_reports(
        self, hours_after_first_checkin_to_inform
    ):
        # iterate through incomplete communications
        for communication in self.env["pms.ses.communication"].search(
            [
                ("state", "=", "incomplete"),
                ("entity", "=", "PV"),
            ]
        ):
            try:
                time_difference = fields.Datetime.now() - communication.create_date
                hours_difference = (
                    time_difference.days * 24 + time_difference.seconds // 3600
                )
                if hours_difference > hours_after_first_checkin_to_inform:
                    # add a note to the reservation
                    communication.reservation_id.sudo().message_post(
                        body=_(
                            "There was't enough guests in the reservation when data "
                            "was sent to SES. Sent to SES with onboard guests"
                        )
                    )
                    data = self.generate_xml_reservations_travellers_report(
                        [communication.reservation_id.id],
                        ignore_some_not_onboard=True,
                    )
                    communication.communication_xml = data
                    data = _string_to_zip_to_base64(data)
                    payload = _generate_payload(
                        communication.reservation_id.pms_property_id.institution_lessor_id,
                        communication.operation,
                        communication.entity,
                        data,
                    )
                    communication.communication_soap = payload
                    communication.communication_time = fields.Datetime.now()

                    soap_response = requests.request(
                        "POST",
                        communication.reservation_id.pms_property_id.ses_url,
                        headers=_get_auth_headers(communication),
                        data=payload,
                        verify=get_module_resource("pms_l10n_es", "static", "cert.pem"),
                    )
                    soap_response.raise_for_status()
                    root = ET.fromstring(soap_response.text)
                    communication.sending_result = root.find(".//descripcion").text
                    communication.response_communication_soap = soap_response.text
                    result_code = root.find(".//codigo").text
                    if result_code == REQUEST_CODE_OK:
                        communication.batch_id = root.find(".//lote").text
                        if communication.operation == CREATE_OPERATION_CODE:
                            communication.state = "to_process"
                        else:
                            communication.state = "processed"
                    else:
                        communication.state = "error_sending"
            except requests.exceptions.HTTPError as http_err:
                _handle_request_exception(communication, http_err)
            except requests.exceptions.RequestException as e:
                _handle_request_exception(communication, e)
            except Exception as e:
                _handle_request_exception(communication, e)

    @api.model
    def ses_process_communications(self):
        for communication in self.env["pms.ses.communication"].search(
            [
                ("state", "=", "to_process"),
            ]
        ):
            try:
                var_xml_get_batch = f"""
                    <con:lotes
                    xmlns:con="http://www.neg.hospedajes.mir.es/consultarComunicacion">
                        <con:lote>{communication.batch_id}</con:lote>
                    </con:lotes>
                """
                communication.query_status_xml = var_xml_get_batch
                data = _string_to_zip_to_base64(var_xml_get_batch)
                payload = _generate_payload(
                    communication.reservation_id.pms_property_id.institution_lessor_id,
                    "C",
                    False,
                    data,
                )
                communication.query_status_soap = payload
                communication.query_status_time = fields.Datetime.now()

                soap_response = requests.request(
                    "POST",
                    communication.reservation_id.pms_property_id.ses_url,
                    headers=_get_auth_headers(communication),
                    data=payload,
                    verify=get_module_resource("pms_l10n_es", "static", "cert.pem"),
                )
                soap_response.raise_for_status()
                root = ET.fromstring(soap_response.text)
                result_code = root.find(".//codigo").text
                communication.response_query_status_soap = soap_response.text
                if result_code == REQUEST_CODE_OK:
                    result_status = root.find(".//codigoEstado").text
                    if result_status == XML_OK:
                        communication.state = "processed"
                        communication.communication_id = root.find(
                            ".//codigoComunicacion"
                        ).text
                        communication.processing_result = root.find(
                            ".//descripcion"
                        ).text
                    elif result_status in [XML_PROCESSING, XML_PENDING]:
                        communication.state = "to_process"
                        communication.processing_result = "Not processed yet"
                    else:
                        communication.state = "error_processing"
                        communication.processing_result = root.find(".//error").text
                # request errors
                else:
                    communication.state = "error_processing"
                    communication.processing_result = root.find(".//descripcion").text
            except requests.exceptions.HTTPError as http_err:
                _handle_request_exception(communication, http_err)
            except requests.exceptions.RequestException as e:
                _handle_request_exception(communication, e)
            except Exception as e:
                _handle_request_exception(communication, e)
