from datetime import datetime

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
        pms_property = self.env["pms.property"].browse(input_param.pmsPropertyId)
        ocr_find_method_name = (
            "_%s_document_process" % pms_property.ocr_checkin_supplier
        )
        if hasattr(pms_property, ocr_find_method_name):
            checkin_data_dict = getattr(pms_property, ocr_find_method_name)(
                input_param.imageBase64Front, input_param.imageBase64Back
            )
        PmsOcrCheckinResult = self.env.datamodels["pms.ocr.checkin.result"]

        return PmsOcrCheckinResult(
            nationality=checkin_data_dict.get("nationality") or None,
            countryId=checkin_data_dict.get("country_id") or None,
            firstname=checkin_data_dict.get("firstname") or None,
            lastname=checkin_data_dict.get("lastname") or None,
            lastname2=checkin_data_dict.get("lastname2") or None,
            gender=checkin_data_dict.get("gender") or None,
            birthdate=datetime.strftime(
                checkin_data_dict.get("birthdate"), "%Y-%m-%dT%H:%M:%S"
            )
            if checkin_data_dict.get("birthdate")
            else None,
            documentType=checkin_data_dict.get("document_type") or None,
            documentExpeditionDate=datetime.strftime(
                checkin_data_dict.get("document_expedition_date"), "%Y-%m-%dT%H:%M:%S"
            )
            if checkin_data_dict.get("document_expedition_date")
            else None,
            documentSupportNumber=checkin_data_dict.get("document_support_number")
            or None,
            documentNumber=checkin_data_dict.get("document_number") or None,
            residenceStreet=checkin_data_dict.get("residence_street") or None,
            residenceCity=checkin_data_dict.get("residence_city") or None,
            countryState=checkin_data_dict.get("country_state") or None,
            documentCountryId=checkin_data_dict.get("document_country_id") or None,
            zip=checkin_data_dict.get("zip") or None,
        )
