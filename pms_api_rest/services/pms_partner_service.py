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
                    gender=partner.gender if partner.gender else None,
                    birthdate=datetime.combine(
                        partner.birthdate_date, datetime.min.time()
                    ).isoformat()
                    if partner.birthdate_date
                    else None,
                    age=partner.age if partner.age else None,
                    residenceStreet=partner.residence_street
                    if partner.residence_street
                    else None,
                    residenceStreet2=partner.residence_street2
                    if partner.residence_street2
                    else None,
                    residenceZip=partner.residence_zip
                    if partner.residence_zip
                    else None,
                    residenceCity=partner.residence_city
                    if partner.residence_city
                    else None,
                    nationality=partner.nationality_id.id
                    if partner.nationality_id
                    else None,
                    residenceStateId=partner.residence_state_id.id
                    if partner.residence_state_id
                    else None,
                    street=partner.street if partner.street else None,
                    street2=partner.street2 if partner.street2 else None,
                    zip=partner.zip if partner.zip else None,
                    countryId=partner.country_id.id if partner.country_id else None,
                    stateId=partner.state_id.id if partner.state_id else None,
                    city=partner.city if partner.city else None,
                    isAgency=partner.is_agency,
                    isCompany=partner.is_company,
                    residenceCountryId=partner.residence_country_id.id
                    if partner.residence_country_id
                    else None,
                    tagIds=partner.category_id.ids if partner.category_id else [],
                    vatNumber=partner.vat if partner.vat else None,
                    vatDocumentType=partner.vat_document_type
                    if partner.vat_document_type
                    else None,
                    website=partner.website if partner.website else None,
                    comment=partner.comment if partner.comment else None,
                    language=partner.lang if partner.lang else None,
                    userId=partner.user_id if partner.user_id else None,
                    paymentTerms=partner.property_payment_term_id
                    if partner.property_payment_term_id
                    else None,
                    pricelistId=partner.property_product_pricelist
                    if partner.property_product_pricelist
                    else None,
                    salesReference=partner.ref if partner.ref else None,
                    saleChannelId=partner.sale_channel_id
                    if partner.sale_channel_id
                    else None,
                    commission=partner.default_commission
                    if partner.default_commission
                    else None,
                    invoicingPolicy=partner.invoicing_policy
                    if partner.invoicing_policy
                    else None,
                    daysAutoInvoice=partner.margin_days_autoinvoice
                    if partner.margin_days_autoinvoice
                    else None,
                )
            )
        return result_partners

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

    @restapi.method(
        [
            (
                [
                    "/<int:partner_id>/deactivate",
                ],
                "PATCH",
            )
        ],
        auth="jwt_api_pms",
    )
    def deactivate_partner(self, partner_id):
        self.env["res.partner"].browse(partner_id).active = False

    @restapi.method(
        [
            (
                [
                    "/<int:partner_id>/activate",
                ],
                "PATCH",
            )
        ],
        auth="jwt_api_pms",
    )
    def activate_partner(self, partner_id):
        self.env["res.partner"].browse(partner_id).active = True

    @restapi.method(
        [
            (
                [
                    "/partner",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.partner.search.param", is_list=False),
        output_param=Datamodel("pms.checkin.partner.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_partner(self, pms_partner_search_params):
        domain = []
        # if pms_partner_search_params.documentType
        #  and pms_partner_search_params.documentNumber:
        #     doc_number = self.env["res.partner.id_number"].search(
        #         [
        #             ("name", "=", pms_partner_search_params.documentNumber),
        #             ("category_id", "=", pms_partner_search_params.documentType)
        #         ]
        #     )
        #     if doc_number.valid_from:
        #         document_expedition_date = doc_number.valid_from.strftime("%d/%m/%Y")
        #     document_type = pms_partner_search_params.documentType
        #     document_number = pms_partner_search_params.documentNumber
        #     domain.append(('id_numbers', 'in', doc_number))
        PmsPartnerInfo = self.env.datamodels["pms.partner.info"]
        if pms_partner_search_params.vatNumber:
            domain.append(("vat", "=", pms_partner_search_params.vatNumber))
        partner = self.env["res.partner"].search(domain)
        if len(partner) > 1:
            partner = partner.filtered("is_company")
        if partner:
            return PmsPartnerInfo(
                id=partner.id,
                name=partner.name if partner.name else None,
                firstname=partner.firstname if partner.firstname else None,
                lastname=partner.lastname if partner.lastname else None,
                lastname2=partner.lastname2 if partner.lastname2 else None,
                email=partner.email if partner.email else None,
                mobile=partner.mobile if partner.mobile else None,
                phone=partner.phone if partner.phone else None,
                gender=partner.gender if partner.gender else None,
                birthdate=datetime.combine(
                    partner.birthdate_date, datetime.min.time()
                ).isoformat()
                if partner.birthdate_date
                else None,
                age=partner.age if partner.age else None,
                residenceStreet=partner.residence_street
                if partner.residence_street
                else None,
                residenceStreet2=partner.residence_street2
                if partner.residence_street2
                else None,
                residenceZip=partner.residence_zip if partner.residence_zip else None,
                residenceCity=partner.residence_city
                if partner.residence_city
                else None,
                nationality=partner.nationality_id.id
                if partner.nationality_id
                else None,
                residenceStateId=partner.residence_state_id.id
                if partner.residence_state_id
                else None,
                street=partner.street if partner.street else None,
                street2=partner.street2 if partner.street2 else None,
                zip=partner.zip if partner.zip else None,
                countryId=partner.country_id.id if partner.country_id else None,
                stateId=partner.state_id.id if partner.state_id else None,
                city=partner.city if partner.city else None,
                isAgency=partner.is_agency,
                isCompany=partner.is_company,
                residenceCountryId=partner.residence_country_id.id
                if partner.residence_country_id
                else None,
                tagIds=partner.category_id.ids if partner.category_id else [],
                vatNumber=partner.vat if partner.vat else None,
                vatDocumentType=partner.vat_document_type
                if partner.vat_document_type
                else None,
                website=partner.website if partner.website else None,
                comment=partner.comment if partner.comment else None,
                language=partner.lang if partner.lang else None,
                userId=partner.user_id if partner.user_id else None,
                paymentTerms=partner.property_payment_term_id
                if partner.property_payment_term_id
                else None,
                pricelistId=partner.property_product_pricelist
                if partner.property_product_pricelist
                else None,
                salesReference=partner.ref if partner.ref else None,
                saleChannelId=partner.sale_channel_id
                if partner.sale_channel_id
                else None,
                commission=partner.default_commission
                if partner.default_commission
                else None,
                invoicingPolicy=partner.invoicing_policy
                if partner.invoicing_policy
                else None,
                daysAutoInvoice=partner.margin_days_autoinvoice
                if partner.margin_days_autoinvoice
                else None,
            )
        else:
            return []

    def mapping_partner_values(self, pms_partner_info):
        vals = dict()
        partner_fields = {
            "name": pms_partner_info.name,
            "firstname": pms_partner_info.firstname,
            "lastname": pms_partner_info.lastname,
            "lastname2": pms_partner_info.lastname2,
            "email": pms_partner_info.email,
            "mobile": pms_partner_info.mobile,
            "phone": pms_partner_info.phone,
            "gender": pms_partner_info.gender,
            "residence_street": pms_partner_info.residenceStreet,
            "residence_street2": pms_partner_info.residenceStreet2,
            "nationality_id": pms_partner_info.nationality,
            "residence_zip": pms_partner_info.zip,
            "residence_city": pms_partner_info.residenceCity,
            "residence_state_id": pms_partner_info.residenceStateId,
            "residence_country_id": pms_partner_info.residenceCountryId,
            "is_agency": pms_partner_info.isAgency,
            "is_company": pms_partner_info.isCompany,
            "vat": pms_partner_info.vatNumber,
            "street": pms_partner_info.street,
            "street2": pms_partner_info.street2,
            "zip": pms_partner_info.zip,
            "city": pms_partner_info.city,
            "state_id": pms_partner_info.stateId,
            "country_id": pms_partner_info.countryId,
            "user_id": pms_partner_info.userId,
            "lang": pms_partner_info.language,
            "comment": pms_partner_info.comment,
            "property_payment_term_id": pms_partner_info.paymentTerms,
            "property_product_pricelist": pms_partner_info.pricelistId,
            "ref": pms_partner_info.salesReference,
            "sale_channel_id": pms_partner_info.saleChannelId,
            "default_commission": pms_partner_info.commission,
            "invoicing_policy": pms_partner_info.invoicingPolicy,
            "margin_days_autoinvoice": pms_partner_info.daysAutoInvoice,
        }
        if pms_partner_info.birthdate:
            birthdate = datetime.strptime(pms_partner_info.birthdate, "%d/%m/%Y")
            birthdate = birthdate.strftime("%Y-%m-%d")
            vals.update({"birthdate_date": birthdate})
        for k, v in partner_fields.items():
            if v:
                vals.update({k: v})
        return vals
