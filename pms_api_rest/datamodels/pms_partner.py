from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsPartnerSearchParam(Datamodel):
    _name = "pms.partner.search.param"
    id = fields.Integer(required=False, allow_none=True)
    vat = fields.String(required=False, allow_none=True)


class PmsPartnerSearchParam(Datamodel):
    _name = "pms.partner.search.param"
    id = fields.Integer(required=False, allow_none=True)
    vat = fields.String(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)


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
    vat = fields.String(required=False, allow_none=True)
    documentType = fields.Integer(required=False, allow_none=True)
    documentNumber = fields.String(required=False, allow_none=True)
    documentExpeditionDate = fields.String(required=False, allow_none=True)
    documentSupportNumber = fields.String(required=False, allow_none=True)
    gender = fields.String(required=False, allow_none=True)
    birthdate = fields.String(required=False, allow_none=True)
    residenceStreet = fields.String(required=False, allow_none=True)
    zip = fields.String(required=False, allow_none=True)
    residenceCity = fields.String(required=False, allow_none=True)
    nationality = fields.Integer(required=False, allow_none=True)
    countryState = fields.Integer(required=False, allow_none=True)
    isAgency = fields.Boolean(required=False, allow_none=True)
    countryChar = fields.String(required=False, allow_none=True)
    countryId = fields.Integer(required=False, allow_none=True)
    countryName = fields.String(required=False, allow_none=True)
    tagIds = fields.List(fields.Integer(required=False, allow_none=True))
    lastStay = fields.String(required=False, allow_none=True)
    website = fields.String(required=False, allow_none=True)

