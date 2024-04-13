import re
from datetime import date, datetime, timedelta

from odoo import _
from odoo.exceptions import ValidationError
from odoo.osv import expression

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

_ref_vat = {
    "al": "J91402501L",
    "ar": "200-5536168-2 or 20055361682",
    "at": "U12345675",
    "au": "83 914 571 673",
    "be": "0477472701",
    "bg": "1234567892",
    "ch": "CHE-123.456.788 TVA or CHE-123.456.788 MWST or CHE-123.456.788 IVA",
    "cl": "76086428-5",
    "co": "213123432-1 or 213.123.432-1",
    "cy": "10259033P",
    "cz": "12345679",
    "de": "123456788",
    "dk": "12345674",
    "do": "1-01-85004-3 or 101850043",
    "ec": "1792060346-001",
    "ee": "123456780",
    "el": "12345670",
    "es": "12345674A",
    "fi": "12345671",
    "fr": "23334175221",
    "gb": "123456782 or 123456782",
    "gr": "12345670",
    "hu": "12345676",
    "hr": "01234567896",
    "ie": "1234567FA",
    "in": "12AAAAA1234AAZA",
    "is": "062199",
    "it": "12345670017",
    "lt": "123456715",
    "lu": "12345613",
    "lv": "41234567891",
    "mc": "53000004605",
    "mt": "12345634",
    "mx": "GODE561231GR8",
    "nl": "123456782B90",
    "no": "123456785",
    "pe": "10XXXXXXXXY or 20XXXXXXXXY or 15XXXXXXXXY or 16XXXXXXXXY or 17XXXXXXXXY",
    "ph": "123-456-789-123",
    "pl": "1234567883",
    "pt": "123456789",
    "ro": "1234567897",
    "rs": "101134702",
    "ru": "123456789047",
    "se": "123456789701",
    "si": "12345679",
    "sk": "2022749619",
    "sm": "24165",
    "tr": "1234567890 (VERGINO) or 17291716060 (TCKIMLIKNO)",
    "ve": "V-12345678-1, V123456781, V-12.345.678-1",
    "xi": "123456782",
}


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

        if pms_partner_search_params.housedNow:
            partners_housed_now = (
                self.env["pms.checkin.partner"]
                .search([("state", "=", "onboard")])
                .mapped("partner_id")
            )
            domain.append(("id", "in", partners_housed_now.ids))
        if pms_partner_search_params.housedLastWeek:
            today = date.today()
            last_week_day = today - timedelta(days=7)
            partners_housed_last_week = (
                self.env["pms.checkin.partner"]
                .search(
                    [
                        "|",
                        "&",
                        ("checkin", ">=", last_week_day),
                        ("checkin", "<=", today),
                        "|",
                        ("checkout", ">=", last_week_day),
                        ("checkout", "<=", today),
                        "|",
                        "&",
                        ("checkin", "<=", last_week_day),
                        ("checkout", "<", today),
                        "&",
                        ("checkin", ">=", last_week_day),
                        ("checkout", ">", today),
                        "|",
                        ("checkin", "<", last_week_day),
                        ("checkout", ">", today),
                    ]
                )
                .mapped("partner_id")
            )
            domain.append(("id", "in", partners_housed_last_week.ids))
        if pms_partner_search_params.housedLastMonth:
            today = date.today()
            last_month_day = today - timedelta(days=30)
            partners_housed_last_month = (
                self.env["pms.checkin.partner"]
                .search(
                    [
                        "|",
                        "&",
                        ("checkin", ">=", last_month_day),
                        ("checkin", "<=", today),
                        "|",
                        ("checkout", ">=", last_month_day),
                        ("checkout", "<=", today),
                        "|",
                        "&",
                        ("checkin", "<=", last_month_day),
                        ("checkout", "<", today),
                        "&",
                        ("checkin", ">=", last_month_day),
                        ("checkout", ">", today),
                        "|",
                        ("checkin", "<", last_month_day),
                        ("checkout", ">", today),
                    ]
                )
                .mapped("partner_id")
            )
            domain.append(("id", "in", partners_housed_last_month.ids))
        if (
            pms_partner_search_params.filterByType
            and pms_partner_search_params.filterByType != "all"
        ):
            if pms_partner_search_params.filterByType == "company":
                domain.append(("is_company", "=", True))
            elif pms_partner_search_params.filterByType == "agency":
                domain.append(("is_agency", "=", True))
            elif pms_partner_search_params.filterByType == "individual":
                domain.append(("is_company", "=", False))
                domain.append(("is_agency", "=", False))

        if pms_partner_search_params.filter:
            subdomains = [
                [("vat", "ilike", pms_partner_search_params.filter)],
                [
                    (
                        "aeat_identification",
                        "ilike",
                        pms_partner_search_params.filter,
                    )
                ],
                [("display_name", "ilike", pms_partner_search_params.filter)],
            ]
            if "@" in pms_partner_search_params.filter:
                subdomains.append(
                    [("email", "ilike", pms_partner_search_params.filter)]
                )
            domain_partner_search_field = expression.OR(subdomains)
            domain = expression.AND([domain, domain_partner_search_field])
        PmsPartnerResults = self.env.datamodels["pms.partner.results"]
        PmsPartnerInfo = self.env.datamodels["pms.partner.info"]
        total_partners = self.env["res.partner"].search_count(domain)

        for partner in self.env["res.partner"].search(
            domain,
            limit=pms_partner_search_params.limit,
            offset=pms_partner_search_params.offset,
        ):
            checkouts = (
                self.env["pms.checkin.partner"]
                .search([("partner_id.id", "=", partner.id)])
                .filtered(lambda x: x.checkout)
                .mapped("checkout")
            )
            doc_number = False
            document_number = False
            document_type = False
            document_support_number = False
            if partner.id_numbers:
                doc_number = partner.id_numbers[0]
            if doc_number:
                if doc_number.name:
                    document_number = doc_number.name
                if doc_number.category_id:
                    document_type = doc_number.category_id.id
                if doc_number.support_number:
                    document_support_number = doc_number.support_number
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
                    documentNumber=document_number if document_number else None,
                    documentType=document_type if document_type else None,
                    documentSupportNumber=document_support_number
                    if document_support_number
                    else None,
                    vatNumber=partner.vat
                    if partner.vat
                    else partner.aeat_identification
                    if partner.aeat_identification
                    else None,
                    vatDocumentType="02"
                    if partner.vat
                    else partner.aeat_identification_type
                    if partner.aeat_identification_type
                    else None,
                    documentExpeditionDate=datetime.combine(
                        doc_number.valid_from, datetime.min.time()
                    ).isoformat()
                    if doc_number and doc_number.valid_from
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
        output_param=Datamodel("pms.transaction.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_partner_payments(self, partner_id):
        partnerPayments = self.env["account.payment"].search(
            [("partner_id", "=", partner_id)]
        )
        PmsTransactiontInfo = self.env.datamodels["pms.transaction.info"]
        payments = []
        for payment in partnerPayments:
            destination_journal_id = False
            if payment.is_internal_transfer:
                destination_journal_id = (
                    payment.pms_api_counterpart_payment_id.journal_id.id
                )
            payments.append(
                PmsTransactiontInfo(
                    id=payment.id,
                    name=payment.name if payment.name else None,
                    amount=payment.amount,
                    journalId=payment.journal_id.id if payment.journal_id else None,
                    destinationJournalId=destination_journal_id
                    if destination_journal_id
                    else None,
                    date=datetime.combine(
                        payment.date, datetime.min.time()
                    ).isoformat(),
                    folioId=payment.folio_ids[0].id if payment.folio_ids else None,
                    partnerId=payment.partner_id.id if payment.partner_id else None,
                    partnerName=payment.partner_id.name if payment.partner_id else None,
                    reference=payment.ref if payment.ref else None,
                    createUid=payment.create_uid.id if payment.create_uid else None,
                    transactionType=payment.pms_api_transaction_type or None,
                    isReconcilied=(payment.reconciled_statements_count > 0),
                    downPaymentInvoiceId=payment.reconciled_invoice_ids.filtered(
                        lambda inv: inv._is_downpayment()
                    ),
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
        output_param=Datamodel("pms.invoice.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_partner_invoices(self, partner_id):
        partnerInvoices = self.env["account.move"].search(
            [
                ("partner_id", "=", partner_id),
                ("move_type", "in", self.env["account.move"].get_invoice_types()),
            ]
        )
        invoices = []
        PmsFolioInvoiceInfo = self.env.datamodels["pms.invoice.info"]
        PmsInvoiceLineInfo = self.env.datamodels["pms.invoice.line.info"]
        if partnerInvoices:
            for move in partnerInvoices:
                move_lines = []
                for move_line in move.invoice_line_ids:
                    move_lines.append(
                        PmsInvoiceLineInfo(
                            id=move_line.id,
                            name=move_line.name if move_line.name else None,
                            quantity=move_line.quantity if move_line.quantity else None,
                            priceUnit=move_line.price_unit
                            if move_line.price_unit
                            else None,
                            total=move_line.price_total
                            if move_line.price_total
                            else None,
                            discount=move_line.discount if move_line.discount else None,
                            displayType=move_line.display_type
                            if move_line.display_type
                            else None,
                            saleLineId=move_line.folio_line_ids[0]
                            if move_line.folio_line_ids
                            else None,
                            isDownPayment=move_line.move_id._is_downpayment(),
                        )
                    )
                move_url = (
                    move.get_proforma_portal_url()
                    if move.state == "draft"
                    else move.get_portal_url()
                )
                portal_url = (
                    self.env["ir.config_parameter"].sudo().get_param("web.base.url")
                    + move_url
                )
                invoice_date = (
                    move.invoice_date.strftime("%d/%m/%Y")
                    if move.invoice_date
                    else move.invoice_date_due.strftime("%d/%m/%Y")
                    if move.invoice_date_due
                    else None
                )
                invoices.append(
                    PmsFolioInvoiceInfo(
                        id=move.id if move.id else None,
                        folioId=move.folio_ids[0] if move.folio_ids else None,
                        name=move.name if move.name else None,
                        amount=round(move.amount_total, 2)
                        if move.amount_total
                        else None,
                        date=invoice_date,
                        state=move.state if move.state else None,
                        paymentState=move.payment_state if move.payment_state else None,
                        partnerName=move.partner_id.name
                        if move.partner_id.name
                        else None,
                        partnerId=move.partner_id.id if move.partner_id.id else None,
                        moveLines=move_lines if move_lines else None,
                        portalUrl=portal_url,
                        moveType=move.move_type,
                        isReversed=move.payment_state == "reversed",
                        isDownPaymentInvoice=move._is_downpayment(),
                        isSimplifiedInvoice=move.journal_id.is_simplified_invoice,
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
        # Clean Document number
        document_number = re.sub(r"[^a-zA-Z0-9]", "", document_number).upper()
        partner = self.env["pms.checkin.partner"]._get_partner_by_document(
            document_number, doc_type
        )
        partners = []
        if partner:
            doc_number = partner.id_numbers.filtered(
                lambda doc: doc.category_id.id == doc_type.id
            )
            PmsCheckinPartnerInfo = self.env.datamodels["pms.checkin.partner.info"]
            partners.append(
                PmsCheckinPartnerInfo(
                    partnerId=partner.id or None,
                    name=partner.name or None,
                    firstname=partner.firstname or None,
                    lastname=partner.lastname or None,
                    lastname2=partner.lastname2 or None,
                    email=partner.email or None,
                    mobile=partner.mobile or None,
                    documentType=doc_type.id or None,
                    documentNumber=doc_number.name or None,
                    documentExpeditionDate=datetime.combine(
                        doc_number.valid_from, datetime.min.time()
                    ).isoformat()
                    if doc_number.valid_from
                    else None,
                    documentSupportNumber=doc_number.support_number or None,
                    documentCountryId=doc_number.country_id.id or None,
                    gender=partner.gender or None,
                    birthdate=datetime.combine(
                        partner.birthdate_date, datetime.min.time()
                    ).isoformat()
                    if partner.birthdate_date
                    else None,
                    residenceStreet=partner.residence_street or None,
                    zip=partner.residence_zip or None,
                    residenceCity=partner.residence_city or None,
                    nationality=partner.nationality_id.id or None,
                    countryId=partner.residence_country_id or None,
                    countryState=partner.residence_state_id.id or None,
                )
            )
        return partners

    @restapi.method(
        [
            (
                [
                    "/check-doc-number/<string:document_number>/"
                    "<int:document_type_id>/<int:country_id>",
                ],
                "GET",
            )
        ],
        auth="jwt_api_pms",
    )
    # REVIEW: create a new datamodel and service for documents?
    def check_document_number(self, document_number, document_type_id, country_id):
        error_mens = False
        country = self.env["res.country"].browse(country_id)
        document_type = self.env["res.partner.id_category"].browse(document_type_id)
        id_number = self.env["res.partner.id_number"].new(
            {
                "name": document_number,
                "category_id": document_type,
            }
        )
        try:
            document_type.validate_id_number(id_number)
        except ValidationError as e:
            error_mens = str(e)
        if document_type.aeat_identification_type in ["02", "04"]:
            Partner = self.env["res.partner"]
            error = not Partner.simple_vat_check(
                country_code=country.code,
                vat_number=document_number,
            )
            if error:
                error_mens = self._construct_check_vat_error_msg(
                    vat_number=document_number, country_code=country.code
                )
        if error_mens:
            raise ValidationError(error_mens)

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
                if partner.vat
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
            if v is not None:
                vals.update({k: v})
        return vals

    def _construct_check_vat_error_msg(self, vat_number, country_code):
        country_code = country_code.lower()
        vat_no = "(##=VAT Number)"
        vat_no = _ref_vat.get(country_code) or vat_no
        if self.env.context.get("company_id"):
            company = self.env["res.company"].browse(self.env.context["company_id"])
        else:
            company = self.env.company
        if company.vat_check_vies:
            return "\n" + _(
                "The VAT number [%(vat)s] either failed the VIES VAT "
                "validation check or did not respect the expected format %(format)s.",
                vat=vat_number,
                format=vat_no,
            )
        return "\n" + _(
            "The VAT number [%(vat)s] does not seem to be valid. "
            "\nNote: the expected format is %(format)s",
            vat=vat_number,
            format=vat_no,
        )
