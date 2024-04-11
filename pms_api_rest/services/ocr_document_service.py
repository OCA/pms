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
    def process_ocr_document(self, input_param):
        pms_property = self.env['pms.property'].browse(input_param.pmsPropertyId)
        ocr_find_method_name = '_%s_document_process' % pms_property.ocr_checkin_supplier
        checkin_data_dict = hasattr(self, ocr_find_method_name)(
            input_param.imageBase64Front,
            input_param.imageBase64Back
        )
        PmsOcrCheckinResult = self.env.datamodels["pms.ocr.checkin.result"]

        return PmsOcrCheckinResult(
            nationality=checkin_data_dict.get('nationality') or None,
            countryId=checkin_data_dict.get('country_id') or None,
            firstname=checkin_data_dict.get('firstname') or None,
            lastname=checkin_data_dict.get('lastname') or None,
            lastname2=checkin_data_dict.get('lastname2') or None,
            gender=checkin_data_dict.get('gender') or None,
            birthdate=checkin_data_dict.get('gender') or None,
            documentType=checkin_data_dict.get('document_type') or None,
            documentExpeditionDate=checkin_data_dict.get('document_expedition_date') or None,
            documentSupportNumber=checkin_data_dict.get('document_support_number') or None,
            documentNumber=checkin_data_dict.get('document_number') or None,
            residenceStreet=checkin_data_dict.get('residence_street') or None,
            residenceCity=checkin_data_dict.get('residence_city') or None,
            countryState=checkin_data_dict.get('country_state') or None,
            documentCountryId=checkin_data_dict.get('document_country_id') or None,
            zip=checkin_data_dict.get('zip') or None
        )

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
