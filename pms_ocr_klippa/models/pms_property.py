import logging
import traceback
from datetime import date, datetime

import requests
from dateutil.relativedelta import relativedelta
from thefuzz import process

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

CHECKIN_FIELDS = {
    "nationality": "partner_id.nationality_id.id",
    "country_id": "partner_id.residence_country_id.id",
    "firstname": "partner_id.firstname",
    "lastname": "partner_id.lastname",
    "lastname2": "partner_id.lastname2",
    "gender": "partner_id.gender",
    "birthdate": "partner_id.birthdate_date",
    "document_type": "document_type_id.id",
    "document_expedition_date": "document_expedition_date",
    "document_support_number": "document_support_number",
    "document_number": "name",
    "residence_street": "partner_id.residence_street",
    "residence_city": "partner_id.residence_city",
    "country_state": "partner_id.residence_state_id.id",
    "document_country_id": "document_country_id",
    "zip": "partner_id.zip",
}


class PmsProperty(models.Model):
    _inherit = "pms.property"

    ocr_checkin_supplier = fields.Selection(selection_add=[("klippa", "Klippa")])

    # flake8: noqa: C901
    def _klippa_document_process(self, image_base_64_front, image_base_64_back=False):
        try:
            ocr_klippa_url = (
                self.env["ir.config_parameter"].sudo().get_param("ocr_klippa_url")
            )
            ocr_klippa_api_key = (
                self.env["ir.config_parameter"].sudo().get_param("ocr_klippa_api_key")
            )
            document = []
            if image_base_64_front:
                document.append(image_base_64_front)
            if image_base_64_back:
                document.append(image_base_64_back)
            if not document:
                raise ValidationError(_("No document image found"))

            headers = {
                "X-Auth-Key": ocr_klippa_api_key,
                "Content-Type": "application/json",
            }
            payload = {
                "document": document,
            }
            request_size = (len(image_base_64_front) if image_base_64_front else 0) + (
                len(image_base_64_back) if image_base_64_back else 0
            )
            log_data = {
                "pms_property_id": self.id,
                "image_base64_front": image_base_64_front,
                "image_base64_back": image_base_64_back,
                "request_datetime": datetime.now(),
                "endpoint": ocr_klippa_url,
                "request_size": request_size,
                "request_headers": str(headers),
            }

            # Call Klippa OCR API
            result = requests.post(
                ocr_klippa_url,
                headers=headers,
                json=payload,
            )
            json_data = result.json()
            log_data.update(
                {
                    "klippa_response": json_data,
                    "klippa_status": json_data.get("result", "error"),
                    "response_datetime": datetime.now(),
                    "response_size": len(str(json_data)),
                    "request_duration": (
                        datetime.now() - log_data["request_datetime"]
                    ).seconds,
                    "request_id": json_data.get("request_id", False),
                }
            )
            if json_data.get("result") != "success":
                raise ValidationError(_("Error calling Klippa OCR API"))
            document_data = json_data["data"]["parsed"]
            init_mapped_datetime = datetime.now()

            mapped_data = self._map_klippa_data(document_data)

            if mapped_data.get("nominatim_status"):
                log_data.update(
                    {
                        "nominatim_status": mapped_data["nominatim_status"],
                    }
                )
                mapped_data.pop("nominatim_status")
            if mapped_data.get("nominatim_response"):
                log_data.update(
                    {
                        "nominatim_response": mapped_data["nominatim_response"],
                    }
                )
                mapped_data.pop("nominatim_response")

            log_data.update(
                {
                    "service_response": mapped_data,
                    "mapped_duration": (datetime.now() - init_mapped_datetime).seconds,
                    "total_duration": (
                        datetime.now() - log_data["request_datetime"]
                    ).seconds,
                    "final_status": "success",
                }
            )
            self.env["klippa.log"].sudo().create(log_data)
            return mapped_data
        except Exception as e:
            log_data.update(
                {
                    "error": traceback.format_exc(),
                    "final_status": "error",
                    "total_duration": (
                        datetime.now() - log_data["request_datetime"]
                    ).seconds,
                }
            )
            self.env["klippa.log"].sudo().create(log_data)
            _logger.error(e)
            return {}

    def _map_klippa_data(self, document_data):
        mapped_data = {}
        key_document_number, key_personal_number = self._get_number_keys(document_data)
        for key, dict_value in document_data.items():
            if dict_value and isinstance(dict_value, dict):
                value = dict_value.get("value", False)
            else:
                continue
            # Residence Address --------------------------------------------------
            if key == "address" and value:
                mapped_data = self._complete_residence_address(value, mapped_data)

            # Document Data --------------------------------------------------
            elif key == "issuing_country" and value:
                mapped_data["document_country_id"] = self._get_country_id(value)
            elif key == "document_type" and value:
                mapped_data["document_type"] = self._get_document_type(
                    klippa_type=value,
                    country_id=self._get_country_id(
                        document_data.get("issuing_country").get("value")
                        if document_data.get("issuing_country")
                        else False
                    ),
                ).id
            elif key == "personal_number" and value:
                mapped_data[key_personal_number] = value
            elif key == "document_number" and value:
                mapped_data[key_document_number] = value
            elif key == "date_of_issue" and value:
                mapped_data["document_expedition_date"] = datetime.strptime(
                    value, "%Y-%m-%dT%H:%M:%S"
                ).date()
            elif (
                key == "date_of_expiry"
                and value
                and not document_data.get("date_of_issue", False)
            ):
                mapped_data["document_expedition_date"] = self._calc_expedition_date(
                    document_class_code=self._get_document_type(
                        klippa_type=document_data.get("document_class_code", False),
                        country_id=self._get_country_id(
                            document_data.get("issuing_country").get("value")
                            if document_data.get("issuing_country")
                            else False
                        ),
                    ),
                    date_of_expiry=value,
                    age=False,
                    date_of_birth=document_data.get("date_of_birth", False),
                )

            # Personal Data --------------------------------------------------
            elif key == "gender" and value:
                if value == "M":
                    mapped_data["gender"] = "male"
                elif value == "F":
                    mapped_data["gender"] = "female"
                else:
                    mapped_data["gender"] = "other"
            elif key == "given_names" and value:
                mapped_data["firstname"] = value
            elif key == "surname" and value:
                mapped_data["lastname"] = self._get_surnames(
                    origin_surname=value,
                )[0]
                mapped_data["lastname2"] = self._get_surnames(
                    origin_surname=value,
                )[1]
            elif key == "date_of_birth" and value:
                mapped_data["birthdate"] = datetime.strptime(
                    value, "%Y-%m-%dT%H:%M:%S"
                ).date()
            elif key == "nationality" and value:
                mapped_data["nationality"] = self._get_country_id(value)

        # If the document number exist and not get the complete checkin information
        # recovery the lost data from the found document
        if mapped_data.get("document_number") and not all(
            [mapped_data.get(field, False) for field in CHECKIN_FIELDS]
        ):
            document = self.env["res.partner.id_number"].search(
                [
                    ("name", "=", mapped_data["document_number"]),
                ],
                limit=1,
            )
            if document:
                mapped_data = self._complete_mapped_from_partner(document, mapped_data)

        return mapped_data

    def _calc_expedition_date(
        self, document_class_code, date_of_expiry, age, date_of_birth
    ):
        result = False
        person_age = False
        if age:
            person_age = age
        elif date_of_birth and date_of_birth.get("value") != "":
            date_of_birth = datetime.strptime(
                date_of_birth.get("value"), "%Y-%m-%dT%H:%M:%S"
            ).date()
            person_age = relativedelta(date.today(), date_of_birth).years
        if date_of_expiry and date_of_expiry != "" and person_age:
            date_of_expiry = datetime.strptime(
                date_of_expiry, "%Y-%m-%dT%H:%M:%S"
            ).date()
            if person_age < 30:
                result = date_of_expiry - relativedelta(years=5)
            elif (
                person_age >= 30
                and document_class_code
                and document_class_code.code == "P"
            ):
                result = date_of_expiry - relativedelta(years=10)
            elif 30 <= person_age < 70:
                result = date_of_expiry - relativedelta(years=10)
        return result if result else False

    def _get_number_keys(self, document_data):
        # Heuristic to identify the mapping of document_number and document_support_number
        # with respect to the personal_number and document_number fields of klippa
        # If the klippa document type is "I", and it is Spanish, then the personal_number
        # we map it against document_number and document_number against document_support_number
        # otherwise, the document_number we map against document_number and the personal_number
        # against document_support_number
        key_document_number = "document_number"
        key_personal_number = "document_support_number"
        if (
            document_data.get("document_type", False)
            and document_data.get("document_type").get("value") == "I"
            and document_data.get("issuing_country", False)
            and document_data.get("issuing_country").get("value") == "ESP"
        ):
            key_document_number = "document_support_number"
            key_personal_number = "document_number"
        return (key_document_number, key_personal_number)

    def _get_document_type(self, klippa_type, country_id):
        # If we hace the issuing country, and document type is configured in the system
        # to be used with the country, we use the country to get the document type
        # If have issuing country and not found document type, we search a document type
        # without country
        # If not have issuing country, we search the document only by klippa code
        document_type = False
        domain = [("klippa_code", "=", klippa_type)]
        if country_id:
            domain.append(("country_ids", "in", country_id))
        document_type = self.env["res.partner.id_category"].search(domain, limit=1)
        if not document_type and country_id:
            document_type = self.env["res.partner.id_category"].search(
                [
                    ("klippa_code", "=", klippa_type),
                    ("country_ids", "=", False),
                ],
            )
        elif not document_type:
            document_type = self.env["res.partner.id_category"].search(
                [
                    ("klippa_code", "=", klippa_type),
                ],
            )
        if len(document_type) > 1:
            # Try find document type by klippa_subtype_code, if not found, get the first
            document_subtype = document_type.filtered(
                lambda dt: dt.klippa_subtype_code
                == document_data.get("document_subtype").get("value")
            )
            document_type = (
                document_subtype[0] if document_subtype else document_type[0]
            )
        if not document_type:
            document_type = self.env.ref("pms.document_type_identification_document")
        return document_type[0] if document_type else False

    def _get_country_id(self, country_code):
        if not country_code:
            return False
        return (
            self.env["res.country"]
            .search([("code_alpha3", "=", country_code)], limit=1)
            .id
        )

    def _get_surnames(self, origin_surname):
        # If origin surname has two or more surnames
        # Get the last word like lastname2 and the rest like lastname
        surnames = origin_surname.split(" ")
        if len(surnames) > 1:
            return (" ".join(surnames[:-1]), surnames[-1])
        return (origin_surname, False)

    def _complete_residence_address(self, value, mapped_data):
        """
        This method tries to complete the residence address with the given data,
        first we use the thefuzz library looking for acceptable matches
        in the province and/or country name.
        Once these data are completed, if the residence address has not been completed
        we try to use the geopy library to complete the address with the data
        """
        street_name = False
        if "street_name" in value:
            mapped_data["residence_street"] = value["street_name"] + (
                " " + value["house_number"] if "house_number" in value else ""
            )
            street_name = value["street_name"]
        if "city" in value:
            mapped_data["residence_city"] = value["city"]
        if "province" in value:
            country_record = self._get_country_id(value.get("country", False))
            domain = []
            if country_record:
                domain.append(("country_id", "=", country_record))
            candidates = process.extractOne(
                value["province"],
                self.env["res.country.state"].search(domain).mapped("name"),
            )
            if candidates[1] >= 90:
                country_state = self.env["res.country.state"].search(
                    domain + [("name", "=", candidates[0])], limit=1
                )
                mapped_data["country_state"] = country_state.id
                if not country_record and country_state:
                    mapped_data["country_id"] = country_state.country_id.id
            else:
                mapped_data["country_state"] = False
        if "country" in value and not mapped_data.get("country_id", False):
            country_record = self._get_country_id(value["country"])
            mapped_data["country_id"] = country_record
        if "postcode" in value:
            mapped_data["zip"] = value["postcode"]
            zip_code = self.env["res.city.zip"].search(
                [
                    ("name", "=", value["postcode"]),
                ]
            )
            if zip_code:
                mapped_data["residence_city"] = (
                    zip_code.city_id.name
                    if not mapped_data.get("residence_city", False)
                    else mapped_data["residence_city"]
                )
                mapped_data["country_state"] = (
                    zip_code.city_id.state_id.id
                    if not mapped_data.get("country_state", False)
                    else mapped_data["country_state"]
                )
                mapped_data["country_id"] = (
                    zip_code.city_id.state_id.country_id.id
                    if not mapped_data.get("country_id", False)
                    else mapped_data["country_id"]
                )

        address_data_dict = {
            "zip": mapped_data.get("zip") or None,
            "country_id": mapped_data.get("country_id") or None,
            "countryState": mapped_data.get("country_state") or None,
            "residence_city": mapped_data.get("residence_city") or None,
            "residence_street": mapped_data.get("residence_street") or None,
        }
        # If we have one ore more values in address_data_dict, but not all,
        # we try to complete the address
        if any(address_data_dict.values()) and not all(address_data_dict.values()):
            params = {
                "format": "json",
                "addressdetails": 1,
                "language": "en",
                "timeout": 5,
                "limit": 1,
            }
            if address_data_dict.get("zip"):
                params["postalcode"] = address_data_dict["zip"]
            if address_data_dict.get("country_id"):
                params["country"] = (
                    self.env["res.country"].browse(address_data_dict["country_id"]).name
                )
            if address_data_dict.get("countryState"):
                params["state"] = (
                    self.env["res.country.state"]
                    .browse(address_data_dict["countryState"])
                    .name
                )
            if address_data_dict.get("residence_city"):
                params["city"] = address_data_dict["residence_city"]

            # Try to complete the address with Nominatim API
            try:
                params = self._get_nominatim_address(params, street_name, mapped_data)
            except Exception as e:
                _logger.error(e)
                mapped_data["nominatim_status"] = "error"
                mapped_data["nominatim_response"] = str(e)
        return mapped_data

    def _get_nominatim_address(self, params, street_name, mapped_data):
        if street_name:
            # Clean street name with mains words
            street_words = street_name.split(" ")
            params["street"] = " ".join(
                [word for word in street_words if len(word) > 2]
            )
        location = requests.get(NOMINATIM_URL, params=params)
        if not location.json() or location.status_code != 200:
            # If not found address, pop the street to try again
            if street_name:
                params.pop("street")
                location = requests.get(NOMINATIM_URL, params=params)
        if location.json() and location.status_code == 200:
            mapped_data["nominatim_response"] = location.json()
            mapped_data["nominatim_status"] = "success"
            location = location.json()[0]
            _logger.info(location)
            if not mapped_data.get("zip", False):
                mapped_data["zip"] = location.get("address", {}).get("postcode", False)
                if mapped_data["zip"]:
                    zip_code = self.env["res.city.zip"].search(
                        [("name", "=", mapped_data["zip"])]
                    )
                    if zip_code:
                        mapped_data["residence_city"] = zip_code.city_id.name
                        mapped_data["country_state"] = zip_code.city_id.state_id.id
                        mapped_data[
                            "country_id"
                        ] = zip_code.city_id.state_id.country_id.id
            if not mapped_data.get("country_id", False):
                country_record = self.env["res.country"].search(
                    [
                        (
                            "code",
                            "=",
                            location.get("address", {})
                            .get("country_code", False)
                            .upper(),
                        )
                    ]
                )
                if not country_record and location.get("address", {}).get(
                    "country", False
                ):
                    country_match = process.extractOne(
                        location.get("address", {}).get("country", False),
                        self.env["res.country"]
                        .with_context(lang="en_US")
                        .search([])
                        .mapped("name"),
                    )
                    if country_match[1] >= 90:
                        country_record = (
                            self.env["res.country"]
                            .with_context(lang="en_US")
                            .search([("name", "=", country_match[0])])
                        )
                mapped_data["country_id"] = country_record.id
            if not mapped_data.get("country_state", False):
                state_name = (
                    location.get("address", {}).get("province")
                    if location.get("address", {}).get("province")
                    else location.get("address", {}).get("state")
                )
                if state_name:
                    country_state_record = process.extractOne(
                        state_name,
                        self.env["res.country.state"].search([]).mapped("name"),
                    )
                    if country_state_record[1] >= 90:
                        country_state = self.env["res.country.state"].search(
                            [("name", "=", country_state_record[0])], limit=1
                        )
                        mapped_data["country_state"] = country_state.id
            if not mapped_data.get("residence_city", False):
                mapped_data["residence_city"] = location.get("address", {}).get(
                    "city", False
                )
            if not mapped_data.get("residence_street", False):
                mapped_data["residence_street"] = location.get("address", {}).get(
                    "road", False
                )
        return mapped_data

    def _complete_mapped_from_partner(self, document, mapped_data):
        for key, field in CHECKIN_FIELDS.items():
            if (
                not mapped_data.get(key, False)
                and document.mapped(field)
                and document.mapped(field)[0]
            ):
                mapped_data[key] = document.mapped(field)[0]
        return mapped_data
