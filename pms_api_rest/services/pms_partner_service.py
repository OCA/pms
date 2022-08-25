from datetime import datetime

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsPartnerService(Component):
    _inherit = "base.rest.service"
    _name = "pms.partner.service"
    _usage = "partners"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.partner.search.param", is_list=False),
        output_param=Datamodel("pms.partner.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_partners(self, pms_partner_search_params):
        result_partners = []
        domain = []
        if pms_partner_search_params.vat:
            domain.append(("vat", "=", pms_partner_search_params.vat))
        if pms_partner_search_params.name:
            domain.append(("name", "ilike", pms_partner_search_params.name))
        PmsPartnerInfo = self.env.datamodels["pms.partner.info"]
        for partner in self.env["res.partner"].search(domain):
            result_partners.append(
                PmsPartnerInfo(
                    id=partner.id,
                    name=partner.name if partner.name else None,
                    firstname=partner.firstname if partner.firstname else None,
                    lastname=partner.lastname if partner.lastname else None,
                    lastname2=partner.lastname2 if partner.lastname2 else None,
                    email=partner.email if partner.email else None,
                    mobile=partner.mobile if partner.mobile else None,
                    phone=partner.phone if partner.phone else None,
                    birthdate=datetime.combine(
                        partner.birthdate_date, datetime.min.time()
                    ).isoformat()
                    if partner.birthdate_date
                    else None,
                    residenceStreet=partner.residence_street
                    if partner.residence_street
                    else None,
                    zip=partner.residence_zip if partner.residence_zip else None,
                    residenceCity=partner.residence_city
                    if partner.residence_city
                    else None,
                    nationality=partner.nationality_id.id
                    if partner.nationality_id
                    else None,
                    countryState=partner.residence_state_id.id
                    if partner.residence_state_id
                    else None,
                    isAgency=partner.is_agency,
                    countryId=partner.residence_country_id.id
                    if partner.residence_country_id
                    else None,
                    countryChar=partner.residence_country_id.code_alpha3
                    if partner.residence_country_id
                    else None,
                    countryName=partner.residence_country_id.name
                    if partner.residence_country_id
                    else None,
                    tagIds=partner.category_id.ids if partner.category_id else [],
                    documentNumbers=partner.id_numbers if partner.id_numbers else [],
                    vat=partner.vat if partner.vat else None,
                    website=partner.website if partner.website else None,
                )
            )
        return result_partners

    # REVIEW: analyze in which service file this method should be
    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "POST",
            )
        ],
        input_param=Datamodel("pms.partner.info", is_list=False),
        auth="jwt_api_pms",
    )
    def create_partner(self, partner_info):
        vals = self.mapping_partner_values(partner_info)
        partner = self.env["res.partner"].create(vals)
        if partner_info.documentNumber:
            doc_type_id = (
                self.env["res.partner.id_category"].search([("name", "=", "DNI")]).id
            )
            self.env["res.partner.id_number"].create(
                {
                    "partner_id": partner.id,
                    "category_id": doc_type_id,
                    "name": partner_info.documentNumber,
                }
            )

    @restapi.method(
        [
            (
                [
                    "/<int:partner_id>",
                ],
                "PATCH",
            )
        ],
        input_param=Datamodel("pms.partner.info", is_list=False),
        auth="jwt_api_pms",
    )
    def write_partner(self, partner_id, partner_info):
        partner = self.env["res.partner"].browse(partner_id)
        if partner:
            partner.write(self.mapping_partner_values(partner_info))
        if partner_info.documentNumber:
            doc_type_id = (
                self.env["res.partner.id_category"].search([("name", "=", "DNI")]).id
            )
            doc_number = self.env["res.partner.id_number"].search(
                [
                    ("partner_id", "=", partner_id),
                    ("name", "=", partner_info.documentNumber),
                    ("category_id", "=", doc_type_id),
                ]
            )
            if not doc_number:
                self.env["res.partner.id_number"].create(
                    {
                        "category_id": doc_type_id,
                        "name": partner_info.documentNumber,
                    }
                )
            else:
                doc_number.write(
                    {
                        "name": partner_info.documentNumber,
                    }
                )

    # REVIEW: analyze in which service file this method should be
    @restapi.method(
        [
            (
                [
                    "/<string:documentType>/<string:documentNumber>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.checkin.partner.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_partner_by_doc_number(self, document_type, document_number):
        doc_number = self.env["res.partner.id_number"].search(
            [("name", "=", document_number), ("category_id", "=", int(document_type))]
        )
        partners = []
        PmsCheckinPartnerInfo = self.env.datamodels["pms.checkin.partner.info"]
        if not doc_number:
            pass
        else:
            if doc_number.valid_from:
                document_expedition_date = doc_number.valid_from.strftime("%d/%m/%Y")
            if doc_number.partner_id.birthdate_date:
                birthdate_date = doc_number.partner_id.birthdate_date.strftime(
                    "%d/%m/%Y"
                )
            partners.append(
                PmsCheckinPartnerInfo(
                    # id=doc_number.partner_id.id,
                    name=doc_number.partner_id.name
                    if doc_number.partner_id.name
                    else None,
                    firstname=doc_number.partner_id.firstname
                    if doc_number.partner_id.firstname
                    else None,
                    lastname=doc_number.partner_id.lastname
                    if doc_number.partner_id.lastname
                    else None,
                    lastname2=doc_number.partner_id.lastname2
                    if doc_number.partner_id.lastname2
                    else None,
                    email=doc_number.partner_id.email
                    if doc_number.partner_id.email
                    else None,
                    mobile=doc_number.partner_id.mobile
                    if doc_number.partner_id.mobile
                    else None,
                    documentType=int(document_type),
                    documentNumber=doc_number.name,
                    documentExpeditionDate=document_expedition_date
                    if doc_number.valid_from
                    else None,
                    documentSupportNumber=doc_number.support_number
                    if doc_number.support_number
                    else None,
                    gender=doc_number.partner_id.gender
                    if doc_number.partner_id.gender
                    else None,
                    birthdate=birthdate_date
                    if doc_number.partner_id.birthdate_date
                    else None,
                    residenceStreet=doc_number.partner_id.residence_street
                    if doc_number.partner_id.residence_street
                    else None,
                    zip=doc_number.partner_id.residence_zip
                    if doc_number.partner_id.residence_zip
                    else None,
                    residenceCity=doc_number.partner_id.residence_city
                    if doc_number.partner_id.residence_city
                    else None,
                    nationality=doc_number.partner_id.nationality_id.id
                    if doc_number.partner_id.nationality_id
                    else None,
                    countryState=doc_number.partner_id.residence_state_id.id
                    if doc_number.partner_id.residence_state_id
                    else None,
                )
            )
        return partners

    def mapping_partner_values(self, pms_partner_info):
        vals = dict()
        partner_fields = {
            "firstname": pms_partner_info.firstname,
            "lastname": pms_partner_info.lastname,
            "email": pms_partner_info.email,
            "mobile": pms_partner_info.mobile,
            "phone": pms_partner_info.phone,
            "gender": pms_partner_info.gender,
            "residence_street": pms_partner_info.residenceStreet,
            "nationality_id": pms_partner_info.nationality,
            "residence_zip": pms_partner_info.zip,
            "residence_city": pms_partner_info.residenceCity,
            "residence_state_id": pms_partner_info.countryState,
            "residence_country_id": pms_partner_info.nationality,
            "is_agency": pms_partner_info.isAgency,
            "vat": pms_partner_info.vat,
            "website": pms_partner_info.website,
        }
        if pms_partner_info.birthdate:
            birthdate = datetime.strptime(pms_partner_info.birthdate, "%d/%m/%Y")
            birthdate = birthdate.strftime("%Y-%m-%d")
            vals.update({"birthdate_date": birthdate})
        for k, v in partner_fields.items():
            if v:
                vals.update({k: v})
        return vals
