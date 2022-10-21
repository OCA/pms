from datetime import datetime

from odoo.osv import expression

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
        output_param=Datamodel("pms.partner.results", is_list=False),
        auth="jwt_api_pms",
    )
    def get_partners(self, pms_partner_search_params):
        result_partners = []
        domain = []

        if pms_partner_search_params.name:
            domain.append(("name", "ilike", pms_partner_search_params.name))
        if pms_partner_search_params.housed:
            partners_housed = (
                self.env["pms.checkin.partner"]
                .search([("state", "=", "onboard")])
                .mapped("partner_id")
            )
            domain.append(("id", "in", partners_housed.ids))
        if pms_partner_search_params.filter:
            domain.append(("display_name", "ilike", pms_partner_search_params.filter))
        if pms_partner_search_params.vatNumberOrName:
            subdomains = [
                [("vat", "ilike", pms_partner_search_params.vatNumberOrName)],
                [
                    (
                        "aeat_identification",
                        "ilike",
                        pms_partner_search_params.vatNumberOrName,
                    )
                ],
                [("display_name", "ilike", pms_partner_search_params.vatNumberOrName)],
            ]
            domain_vat_or_name = expression.OR(subdomains)
            domain = expression.AND([domain, domain_vat_or_name])

        PmsPartnerResults = self.env.datamodels["pms.partner.results"]
        PmsPartnerInfo = self.env.datamodels["pms.partner.info"]
        total_partners = self.env["res.partner"].search_count(domain)

        for partner in self.env["res.partner"].search(
            domain,
            order=pms_partner_search_params.orderBy,
            limit=pms_partner_search_params.limit,
            offset=pms_partner_search_params.offset,
        ):
            checkouts = (
                self.env["pms.checkin.partner"]
                .search([("partner_id.id", "=", partner.id)])
                .filtered(lambda x: x.checkout)
                .mapped("checkout")
            )
            result_partners.append(
                PmsPartnerInfo(
                    id=partner.id,
                    name=partner.name if partner.name else None,
                    firstname=partner.firstname if partner.firstname else None,
                    lastname=partner.lastname if partner.lastname else None,
                    lastname2=partner.lastname2 if partner.lastname2 else None,
                    email=partner.email if partner.email else None,
                    phone=partner.phone if partner.phone else None,
                    gender=partner.gender if partner.gender else None,
                    birthdate=datetime.combine(
                        partner.birthdate_date, datetime.min.time()
                    ).isoformat()
                    if partner.birthdate_date
                    else None,
                    age=partner.age if partner.age else None,
                    mobile=partner.mobile if partner.mobile else None,
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
                    vatNumber=partner.vat
                    if partner.vat
                    else partner.aeat_identification
                    if partner.aeat_identification
                    else None,
                    vatDocumentType="02"
                    if partner.vat_document_type
                    else partner.aeat_identification_type
                    if partner.aeat_identification_type
                    else None,
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
                    invoicingMonthDay=partner.invoicing_month_day
                    if partner.invoicing_month_day
                    else None,
                    invoiceToAgency=partner.invoice_to_agency
                    if partner.invoice_to_agency
                    else None,
                    tagIds=partner.category_id.ids if partner.category_id else [],
                    lastStay=max(checkouts).strftime("%d/%m/%Y") if checkouts else "",
                )
            )
        return PmsPartnerResults(partners=result_partners, total=total_partners)

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
        return partner.id

    @restapi.method(
        [
            (
                [
                    "/p/<int:partner_id>",
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

    @restapi.method(
        [
            (
                [
                    "/<int:partner_id>/payments",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.payment.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_partner_payments(self, partner_id):
        partnerPayments = self.env["account.payment"].search(
            [("partner_id", "=", partner_id)]
        )
        PmsPaymentInfo = self.env.datamodels["pms.payment.info"]
        payments = []
        for payment in partnerPayments:
            payments.append(
                PmsPaymentInfo(
                    id=payment.id,
                    amount=round(payment.amount, 2),
                    journalId=payment.journal_id.id,
                    date=payment.date.strftime("%d/%m/%Y"),
                    reference=payment.ref,
                )
            )
        return payments

    @restapi.method(
        [
            (
                [
                    "/<int:partner_id>/invoices",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.account.move.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_partner_invoices(self, partner_id):
        partnerInvoices = self.env["account.move"].search(
            [
                ("partner_id", "=", partner_id),
                ("move_type", "in", self.env["account.move"].get_invoice_types()),
            ]
        )
        PmsAcoountMoveInfo = self.env.datamodels["pms.account.move.info"]
        invoices = []
        for invoice in partnerInvoices:
            invoices.append(
                PmsAcoountMoveInfo(
                    id=invoice.id,
                    name=invoice.name,
                    amount=round(invoice.amount_total, 2),
                    date=invoice.date.strftime("%d/%m/%Y"),
                    state=invoice.state,
                    paymentState=invoice.payment_state
                    if invoice.payment_state
                    else None,
                )
            )
        return invoices

    @restapi.method(
        [
            (
                [
                    "/<string:documentType>/<string:documentNumber>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.partner.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_partner_by_doc_number(self, document_type, document_number):
        doc_type = self.env["res.partner.id_category"].search(
            [("id", "=", document_type)]
        )
        doc_number = self.env["res.partner.id_number"].search(
            [("name", "=", document_number), ("category_id", "=", doc_type.id)]
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
                    id=doc_number.partner_id.id,
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
                    documentType=doc_type.id,
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
                    countryId=doc_number.partner_id.residence_country_id
                    if doc_number.partner_id.residence_country_id
                    else None,
                    countryState=doc_number.partner_id.residence_state_id.id
                    if doc_number.partner_id.residence_state_id
                    else None,
                )
            )
        return partners

    @restapi.method(
        [
            (
                [
                    "/p/<int:partner_id>/deactivate",
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
                    "/p/<int:partner_id>/activate",
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
                    "/<int:partner_id>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.partner.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_partner(self, partner_id):
        PmsPartnerInfo = self.env.datamodels["pms.partner.info"]
        partner = self.env["res.partner"].browse(partner_id)
        if not partner:
            return PmsPartnerInfo()
        else:
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
                vatNumber=partner.vat
                if partner.vat
                else partner.aeat_identification
                if partner.aeat_identification
                else None,
                vatDocumentType="02"
                if partner.vat_document_type
                else partner.aeat_identification_type
                if partner.aeat_identification_type
                else None,
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
                invoicingMonthDay=partner.invoicing_month_day
                if partner.invoicing_month_day
                else None,
                invoiceToAgency=partner.invoice_to_agency
                if partner.invoice_to_agency
                else None,
            )

    def mapping_partner_values(self, pms_partner_info):
        vals = dict()
        partner_fields = {
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
            "residence_zip": pms_partner_info.residenceZip,
            "residence_city": pms_partner_info.residenceCity,
            "residence_state_id": pms_partner_info.residenceStateId,
            "residence_country_id": pms_partner_info.residenceCountryId,
            "is_agency": pms_partner_info.isAgency,
            "is_company": pms_partner_info.isCompany,
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
            "invoicing_month_day": pms_partner_info.invoicingMonthDay,
            "invoice_to_agency": pms_partner_info.invoiceToAgency,
        }

        if (
            pms_partner_info.isAgency
            or pms_partner_info.isCompany
            or (
                pms_partner_info.vatDocumentType == "02"
                or pms_partner_info.vatDocumentType == "04"
            )
        ):
            partner_fields.update(
                {
                    "vat": pms_partner_info.vatNumber,
                    "vat_document_type": "vat",
                }
            )
        else:
            partner_fields.update(
                {
                    "aeat_identification_type": pms_partner_info.vatDocumentType,
                    "aeat_identification": pms_partner_info.vatNumber,
                }
            )

        if pms_partner_info.birthdate:
            birthdate = datetime.strptime(pms_partner_info.birthdate, "%d/%m/%Y")
            birthdate = birthdate.strftime("%Y-%m-%d")
            vals.update({"birthdate_date": birthdate})
        for k, v in partner_fields.items():
            if v:
                vals.update({k: v})
        return vals
