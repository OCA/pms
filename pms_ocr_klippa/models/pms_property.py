from datetime import date, datetime

import requests
from dateutil.relativedelta import relativedelta

from odoo import _, fields, models
from odoo.exceptions import ValidationError


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
        if image_base_64_back:
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
                if "street_name" in value:
                    mapped_data["residence_street"] = value["street_name"] + (
                        " " + value["house_number"] if "house_number" in value else ""
                    )
                if "city" in value:
                    mapped_data["residence_city"] = value["city"]
                if "postcode" in value:
                    mapped_data["zip"] = value["postcode"]
                if "province" in value:
                    mapped_data["residence_state_id"] = (
                        self.env["res.country.state"]
                        .search(
                            [
                                ("name", "ilike", value["province"]),
                                (
                                    "country_id",
                                    "=",
                                    self._get_country_id(value.get("country", False)),
                                ),
                            ]
                        )
                        .id
                        or False
                    )

            # Document Data --------------------------------------------------
            elif key == "issuing_country" and value:
                mapped_data["document_country_id"] = self._get_country_id(value)
            elif key == "document_number" and value:
                mapped_data["document_support_number"] = value
            elif key == "document_type" and value:
                mapped_data["document_type"] = self._get_document_type(
                    klippa_type=value,
                    klippa_subtype=document_data.get("document_subtype", False),
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
                mapped_data["document_expiration_date"] = self._calc_expedition_date(
                    document_class_code=self._get_document_type(
                        klippa_type=document_data.get("document_class_code", False),
                        klippa_subtype=document_data.get("document_subtype", False),
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

    def _calc_expedition_date(self, document_type, date_of_expiry, age, date_of_birth):
        result = False
        person_age = False
        if age and age.value != "":
            person_age = int(age.value)
        elif date_of_birth and date_of_birth.value != "":
            date_of_birth = datetime.strptime(
                date_of_birth.value.replace("-", "/"), "%Y-%m-%dT%H:%M:%S"
            ).date()
            person_age = relativedelta(date.today(), date_of_birth).years
        if date_of_expiry and date_of_expiry.value != "" and person_age:
            date_of_expiry = datetime.strptime(
                date_of_expiry.value.replace("-", "/"), "%Y-%m-%dT%H:%M:%S"
            ).date()
            if person_age < 30:
                result = date_of_expiry - relativedelta(years=5)
            elif person_age >= 30 and document_type and document_type.code == "P":
                result = date_of_expiry - relativedelta(years=10)
            elif 30 <= person_age < 70:
                result = date_of_expiry - relativedelta(years=10)
        return result.isoformat() if result else False

    def _get_document_type(self, klippa_type, klippa_subtype):
        document_type_ids = self.env["res.partner.id_category"].search(
            [
                ("klippa_code", "=", klippa_type),
            ]
        )
        if not document_type_ids:
            raise ValidationError(_(f"Document type not found: {klippa_type}"))
        document_type_id = document_type_ids[0]
        if len(document_type_ids) > 1:
            document_type_id = document_type_ids.filtered(
                lambda r: r.klippa_subtype_code == klippa_subtype
            ).id
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
