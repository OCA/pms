from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class PmsPartnerSearchParam(Datamodel):
    _name = "pms.partner.search.param"
    _inherit = "pms.rest.metadata"
    id = fields.Integer(required=False, allow_none=True)
    vatNumberOrName = fields.String(required=False, allow_none=True)
    documentType = fields.Integer(required=False, allow_none=True)
    documentNumber = fields.String(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    housed = fields.Boolean(required=False, allow_none=True)
    filter = fields.String(required=False, allow_none=True)
    filterByType = fields.String(required=False, allow_none=True)


class PmsPartnerInfo(Datamodel):
    _name = "pms.partner.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    firstname = fields.String(required=False, allow_none=True)
    lastname = fields.String(required=False, allow_none=True)
    lastname2 = fields.String(required=False, allow_none=True)
    email = fields.String(required=False, allow_none=True)
    mobile = fields.String(required=False, allow_none=True)
    phone = fields.String(required=False, allow_none=True)
    documentType = fields.Integer(required=False, allow_none=True)
    documentNumber = fields.String(required=False, allow_none=True)
    documentExpeditionDate = fields.String(required=False, allow_none=True)
    documentSupportNumber = fields.String(required=False, allow_none=True)
    gender = fields.String(required=False, allow_none=True)
    birthdate = fields.String(required=False, allow_none=True)
    age = fields.Integer(required=False, allow_none=True)
    residenceStreet = fields.String(required=False, allow_none=True)
    residenceStreet2 = fields.String(required=False, allow_none=True)
    residenceCity = fields.String(required=False, allow_none=True)
    residenceZip = fields.String(required=False, allow_none=True)
    nationality = fields.Integer(required=False, allow_none=True)
    residenceStateId = fields.Integer(required=False, allow_none=True)
    isAgency = fields.Boolean(required=False, allow_none=True)
    isCompany = fields.Boolean(required=False, allow_none=True)
    street = fields.String(required=False, allow_none=True)
    street2 = fields.String(required=False, allow_none=True)
    zip = fields.String(required=False, allow_none=True)
    city = fields.String(required=False, allow_none=True)
    stateId = fields.Integer(required=False, allow_none=True)
    countryId = fields.Integer(required=False, allow_none=True)
    residenceCountryId = fields.Integer(required=False, allow_none=True)
    vatNumber = fields.String(required=False, allow_none=True)
    vatDocumentType = fields.String(required=False, allow_none=True)
    comment = fields.String(required=False, allow_none=True)
    language = fields.String(required=False, allow_none=True)
    userId = fields.Integer(required=False, allow_none=True)
    paymentTerms = fields.Integer(required=False, allow_none=True)
    pricelistId = fields.Integer(required=False, allow_none=True)
    salesReference = fields.String(required=False, allow_none=True)
    saleChannelId = fields.Integer(required=False, allow_none=True)
    commission = fields.Integer(required=False, allow_none=True)
    invoicingPolicy = fields.String(required=False, allow_none=True)
    daysAutoInvoice = fields.Integer(required=False, allow_none=True)
    invoicingMonthDay = fields.Integer(required=False, allow_none=True)
    invoiceToAgency = fields.String(required=False, allow_none=True)
    tagIds = fields.List(fields.Integer(required=False, allow_none=True))
    lastStay = fields.String(required=False, allow_none=True)


class PmsPartnerResults(Datamodel):
    _name = "pms.partner.results"
    partners = fields.List(NestedModel("pms.partner.info"))
    total = fields.Integer(required=False, allow_none=True)
