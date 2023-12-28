from datetime import date, datetime

from dateutil.relativedelta import relativedelta
from regula.documentreader.webclient import (
    DocumentReaderApi,
    ProcessParams,
    RecognitionRequest,
    Result,
    Scenario,
    TextFieldType,
)

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsOcr(Component):
    _inherit = "base.rest.service"
    _name = "ocr.document.service"
    _usage = "ocr-document"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.ocr.input"),
        output_param=Datamodel("pms.ocr.checkin.result", is_list=False),
        auth="jwt_api_pms",
    )
    def process_ocr_document_regula(self, input_param):
        PmsOcrCheckinResult = self.env.datamodels["pms.ocr.checkin.result"]
        pms_ocr_checkin_result = PmsOcrCheckinResult()
        ocr_regula_url = (
            self.env["ir.config_parameter"].sudo().get_param("ocr_regula_url")
        )
        with DocumentReaderApi(host=ocr_regula_url) as api:
            params = ProcessParams(
                scenario=Scenario.FULL_PROCESS,
                result_type_output=[
                    Result.TEXT,
                    Result.STATUS,
                    Result.VISUAL_TEXT,
                    Result.DOCUMENT_TYPE,
                ],
            )
            request = RecognitionRequest(
                process_params=params, images=[input_param.imageBase64]
            )
            response = api.process(request)
            if response.text and response.text.field_list:
                # for elemento in response.text.field_list:
                #     print("campo: ", elemento.field_name)
                #     print("valor: ", elemento.value)
                #     print('-')
                id_country_spain = (
                    self.env["res.country"].search([("code", "=", "ES")]).id
                )
                country_id = self.process_nationality(
                    response.text.get_field(TextFieldType.NATIONALITY),
                    response.text.get_field(TextFieldType.NATIONALITY_CODE),
                    response.text.get_field(TextFieldType.NATIONALITY_CODE_NUMERIC),
                )
                firstname, lastname, lastname2 = self.process_name(
                    id_country_spain,
                    country_id,
                    response.text.get_field(TextFieldType.GIVEN_NAMES),
                    response.text.get_field(TextFieldType.FIRST_SURNAME),
                    response.text.get_field(TextFieldType.SECOND_SURNAME),
                    response.text.get_field(TextFieldType.SURNAME),
                    response.text.get_field(TextFieldType.SURNAME_AND_GIVEN_NAMES),
                )
                if country_id:
                    pms_ocr_checkin_result.nationality = country_id
                if firstname:
                    pms_ocr_checkin_result.firstname = firstname
                if lastname:
                    pms_ocr_checkin_result.lastname = lastname
                if lastname2:
                    pms_ocr_checkin_result.lastname2 = lastname2
                gender = response.text.get_field(TextFieldType.SEX)
                if gender and gender.value != "":
                    pms_ocr_checkin_result.gender = (
                        "male"
                        if gender.value == "M"
                        else "female"
                        if gender.value == "F"
                        else "other"
                    )
                date_of_birth = response.text.get_field(TextFieldType.DATE_OF_BIRTH)
                if date_of_birth and date_of_birth.value != "":
                    pms_ocr_checkin_result.birthdate = (
                        datetime.strptime(
                            date_of_birth.value.replace("-", "/"), "%Y/%m/%d"
                        )
                        .date()
                        .isoformat()
                    )
                date_of_expiry = response.text.get_field(TextFieldType.DATE_OF_EXPIRY)
                age = response.text.get_field(TextFieldType.AGE)
                document_class_code = response.text.get_field(
                    TextFieldType.DOCUMENT_CLASS_CODE
                )
                if (
                    document_class_code
                    and document_class_code.value != ""
                    and document_class_code.value == "P"
                ):
                    pms_ocr_checkin_result.documentType = (
                        self.env["res.partner.id_category"]
                        .search([("code", "=", "P")])
                        .id
                    )
                date_of_issue = response.text.get_field(TextFieldType.DATE_OF_ISSUE)
                if country_id == id_country_spain and (
                    not date_of_issue or date_of_issue.value == ""
                ):
                    date_of_issue = self.calc_expedition_date(
                        document_class_code,
                        date_of_expiry,
                        age,
                        date_of_birth,
                    )
                    pms_ocr_checkin_result.documentExpeditionDate = date_of_issue
                elif date_of_issue and date_of_issue.value != "":
                    pms_ocr_checkin_result.documentExpeditionDate = (
                        date_of_issue.value.replace("-", "/")
                    )
                support_number, document_number = self.proccess_document_number(
                    id_country_spain,
                    country_id,
                    document_class_code,
                    response.text.get_field(TextFieldType.DOCUMENT_NUMBER),
                    response.text.get_field(TextFieldType.PERSONAL_NUMBER),
                )
                if support_number:
                    pms_ocr_checkin_result.documentSupportNumber = support_number
                if document_number:
                    pms_ocr_checkin_result.documentNumber = document_number
                address_street, address_city, address_area = self.process_address(
                    id_country_spain,
                    country_id,
                    response.text.get_field(TextFieldType.ADDRESS_STREET),
                    response.text.get_field(TextFieldType.ADDRESS_CITY),
                    response.text.get_field(TextFieldType.ADDRESS_AREA),
                    response.text.get_field(TextFieldType.ADDRESS),
                )
                if address_street:
                    pms_ocr_checkin_result.residenceStreet = address_street
                if address_city:
                    pms_ocr_checkin_result.residenceCity = address_city
                if address_area:
                    pms_ocr_checkin_result.countryState = address_area
        return pms_ocr_checkin_result

    def process_nationality(
        self, nationality, nationality_code, nationality_code_numeric
    ):
        country_id = False
        country = False
        if nationality_code_numeric and nationality_code_numeric.value != "":
            country = self.env["res.country"].search(
                [("code_numeric", "=", nationality_code_numeric.value)]
            )
        elif nationality_code and nationality_code.value != "":
            country = self.env["res.country"].search(
                [("code_alpha3", "=", nationality_code.value)]
            )
        elif nationality and nationality.value != "":
            country = self.env["res.country"].search([("name", "=", nationality.value)])

        if country:
            country_id = country.id

        return country_id

    def process_address(
        self,
        id_country_spain,
        country_id,
        address_street,
        address_city,
        address_area,
        address,
    ):
        res_address_street = False
        res_address_city = False
        res_address_area = False
        state = False
        if country_id == id_country_spain:
            if address_street and address_street.value != "":
                res_address_street = address_street.value
            if address_city and address_city.value != "":
                res_address_city = address_city.value
            if address_area and address_area.value != "":
                res_address_area = address_area.value
            if (
                address
                and address != ""
                and not (all([address_street, address_city, address_area]))
            ):
                address = address.value.replace("^", " ")
                address_list = address.split(" ")
                if not res_address_area:
                    res_address_area = address_list[-1]
                if not res_address_city:
                    res_address_city = address_list[-2]
                if not res_address_street:
                    res_address_street = address.replace(
                        res_address_area, "", 1
                    ).replace(res_address_city, "", 1)
            if res_address_area:
                state = self.env["res.country.state"].search(
                    [("name", "ilike", res_address_area)]
                )
                if state and len(state) == 1:
                    state = state.id
        else:
            if address and address.value != "":
                res_address_street = address.value.replace("^", " ")
        return res_address_street, res_address_city, state

    def process_name(
        self,
        id_country_spain,
        country_id,
        given_names,
        first_surname,
        second_surname,
        surname,
        surname_and_given_names,
    ):
        firstname = False
        lastname = False
        lastname2 = False

        if surname_and_given_names.value and surname_and_given_names.value != "":
            surname_and_given_names = surname_and_given_names.value.replace("^", " ")

        if given_names and given_names.value != "":
            firstname = given_names.value

        if first_surname and first_surname.value != "":
            lastname = first_surname.value

        if second_surname and second_surname.value != "":
            lastname2 = second_surname.value

        if country_id == id_country_spain and not (
            all([firstname, lastname, lastname2])
        ):
            if surname and surname.value != "":
                lastname = lastname if lastname else surname.value.split(" ")[0]
                lastname2 = lastname2 if lastname2 else surname.value.split(" ")[1:][0]
                if (
                    surname_and_given_names
                    and surname_and_given_names != ""
                    and not firstname
                ):
                    firstname = surname_and_given_names.replace(
                        lastname, "", 1
                    ).replace(lastname2, "", 1)
            elif surname_and_given_names and surname_and_given_names != "":
                lastname = (
                    lastname if lastname else surname_and_given_names.split(" ")[0]
                )
                lastname2 = (
                    lastname2 if lastname2 else surname_and_given_names.split(" ")[1]
                )
                firstname = (
                    firstname
                    if firstname
                    else surname_and_given_names.replace(lastname, "", 1).replace(
                        lastname2, "", 1
                    )
                )
        elif (
            country_id
            and country_id != id_country_spain
            and not (all([firstname, lastname]))
        ):
            if surname and surname.value != "":
                lastname = lastname if lastname else surname.value
                if (
                    surname_and_given_names
                    and surname_and_given_names != ""
                    and not firstname
                ):
                    firstname = surname_and_given_names.replace(lastname, "", 1)
            elif surname_and_given_names and surname_and_given_names != "":
                lastname = (
                    lastname if lastname else surname_and_given_names.split(" ")[0]
                )
                firstname = (
                    firstname
                    if firstname
                    else surname_and_given_names.replace(lastname, "", 1)
                )
        return firstname, lastname, lastname2

    def calc_expedition_date(
        self, document_class_code, date_of_expiry, age, date_of_birth
    ):
        result = False
        person_age = False
        if age and age.value != "":
            person_age = int(age.value)
        elif date_of_birth and date_of_birth.value != "":
            date_of_birth = datetime.strptime(
                date_of_birth.value.replace("-", "/"), "%Y/%m/%d"
            ).date()
            person_age = relativedelta(date.today(), date_of_birth).years
        if date_of_expiry and date_of_expiry.value != "" and person_age:
            date_of_expiry = datetime.strptime(
                date_of_expiry.value.replace("-", "/"), "%Y/%m/%d"
            ).date()
            if person_age < 30:
                result = date_of_expiry - relativedelta(years=5)
            elif (
                person_age >= 30
                and document_class_code
                and document_class_code.value == "P"
            ):
                result = date_of_expiry - relativedelta(years=10)
            elif 30 <= person_age < 70:
                result = date_of_expiry - relativedelta(years=10)
        return result.isoformat() if result else False

    def proccess_document_number(
        self,
        id_country_spain,
        country_id,
        document_class_code,
        document_number,
        personal_number,
    ):
        res_support_number = False
        res_document_number = False
        if personal_number and personal_number.value != "":
            res_document_number = personal_number.value
        if document_number and document_number.value != "":
            res_support_number = document_number.value
        if (
            country_id == id_country_spain
            and document_class_code
            and document_class_code.value != "P"
        ):
            return res_support_number, res_document_number
        else:
            return False, res_support_number
