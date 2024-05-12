import logging
from datetime import date, datetime

import requests
from dateutil.relativedelta import relativedelta
from geopy.geocoders import Nominatim
from thefuzz import process

from odoo import _, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PmsProperty(models.Model):
    _inherit = "pms.property"

    ocr_checkin_supplier = fields.Selection(selection_add=[("klippa", "Klippa")])

    # flake8: noqa: C901
    def _klippa_document_process(self, image_base_64_front, image_base_64_back=False):
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

        # Call Klippa OCR API
        result = requests.post(
            ocr_klippa_url,
            headers=headers,
            json=payload,
        )
        json_data = result.json()
        if json_data.get("result") != "success":
            raise ValidationError(_("Error calling Klippa OCR API"))
        document_data = json_data["data"]["parsed"]
        mapped_data = {}
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
            elif key == "document_number" and value:
                mapped_data["document_support_number"] = value
            elif key == "document_type" and value:
                mapped_data["document_type"] = self._get_document_type(
                    klippa_type=value,
                    country_id=self._get_country_id(
                        document_data.get("issuing_country").get("value")
                        if document_data.get("issuing_country")
                        else False
                    ),
                )
            elif key == "personal_number" and value:
                mapped_data["document_number"] = value
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

    def _get_document_type(self, klippa_type, country_id):
        document_type_id = False
        document_type_ids = self.env["res.partner.id_category"].search(
            [
                ("klippa_code", "=", klippa_type),
            ]
        )
        if not document_type_ids:
            raise ValidationError(_(f"Document type not found: {klippa_type}"))

        if len(document_type_ids) > 1:
            document_type_id = document_type_ids.filtered(
                lambda r: country_id in r.country_ids.ids
            )
        if not document_type_id:
            document_type_id = document_type_ids.filtered(lambda r: not r.country_ids)[
                0
            ]
        return document_type_id

    def _get_country_id(self, country_code):
        return (
            self.env["res.country"]
            .search([("code_alpha3", "=", country_code)], limit=1)
            .id
        )

    def _get_surnames(self, origin_surname):
        # If origin surname has two or more surnames
        if " " in origin_surname:
            return origin_surname.split(" ")
        else:
            return [origin_surname, ""]

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
                    domain + [("name", "=", candidates[0])]
                )
                mapped_data["residence_state_id"] = country_state.id
                if not country_record:
                    mapped_data["country_id"] = country_state.country_id.id
            else:
                mapped_data["residence_state_id"] = None
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
                mapped_data["residence_state_id"] = (
                    zip_code.city_id.state_id.id
                    if not mapped_data.get("residence_state_id", False)
                    else mapped_data["residence_state_id"]
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
            geolocator = Nominatim(user_agent="roomdoo_pms")
            search_address_str = f"{street_name}, {mapped_data.get('residence_city', '')}, {mapped_data.get('zip', '')}, {mapped_data.get('country_id', '')}"
            location = geolocator.geocode(
                search_address_str,
                addressdetails=True,
                timeout=5,
                language="en",
            )
            if not location:
                street_words = street_name.split(" ")
                street_words = [word for word in street_words if len(word) > 2]
                while street_words and not location:
                    street_name = " ".join(street_words)
                    search_address_str = f"{street_name}, {mapped_data.get('residence_city', '')}, {mapped_data.get('zip', '')}, {mapped_data.get('country_id', '')}"
                    location = geolocator.geocode(
                        search_address_str,
                        addressdetails=True,
                        timeout=5,
                        language="en",
                    )
                    street_words.pop(0)
            if location:
                if not mapped_data.get("zip", False):
                    mapped_data["zip"] = location.raw.get("address", {}).get(
                        "postcode", False
                    )
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
                    country_match_name = process.extractOne(
                        location.raw.get("address", {}).get("country", False),
                        self.env["res.country"]
                        .with_context(lang="en_US")
                        .search([])
                        .mapped("name"),
                    )
                    if country_match_name[1] >= 90:
                        country_record = (
                            self.env["res.country"]
                            .with_context(lang="en_US")
                            .search([("name", "=", country_match_name[0])])
                        )
                        mapped_data["country_id"] = country_record.id
                if not mapped_data.get("country_state", False):
                    state_name = (
                        location.raw.get("address", {}).get("prorvince")
                        if location.raw.get("address", {}).get("province")
                        else location.raw.get("address", {}).get("state")
                    )
                    if state_name:
                        country_state_record = process.extractOne(
                            state_name,
                            self.env["res.country.state"].search([]).mapped("name"),
                        )
                        if country_state_record[1] >= 90:
                            country_state = self.env["res.country.state"].search(
                                [("name", "=", country_state_record[0])]
                            )
                            mapped_data["country_state"] = country_state.id
                if not mapped_data.get("residence_city", False):
                    mapped_data["residence_city"] = location.raw.get("address", {}).get(
                        "city", False
                    )
                if not mapped_data.get("residence_street", False):
                    mapped_data["residence_street"] = location.raw.get(
                        "address", {}
                    ).get("road", False)
        return mapped_data
