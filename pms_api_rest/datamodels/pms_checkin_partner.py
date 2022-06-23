from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsCheckinPartnerInfo(Datamodel):
    _name = "pms.checkin.partner.info"
    id = fields.Integer(required=False, allow_none=True)
    reservationId = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    firstname = fields.String(required=False, allow_none=True)
    lastname = fields.String(required=False, allow_none=True)
    lastname2 = fields.String(required=False, allow_none=True)
    email = fields.String(required=False, allow_none=True)
    mobile = fields.String(required=False, allow_none=True)
    documentType = fields.String(required=False, allow_none=True)
    documentNumber = fields.String(required=False, allow_none=True)
    documentExpeditionDate = fields.String(required=False, allow_none=True)
    documentSupportNumber = fields.String(required=False, allow_none=True)
    gender = fields.String(required=False, allow_none=True)
    birthdate = fields.String(required=False, allow_none=True)
    residenceStreet = fields.String(required=False, allow_none=True)
    zip = fields.String(required=False, allow_none=True)
    residenceCity = fields.String(required=False, allow_none=True)
    nationality = fields.String(required=False, allow_none=True)
    countryState = fields.String(required=False, allow_none=True)
