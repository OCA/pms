from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsOcrInput(Datamodel):
    _name = "pms.ocr.input"
    imageBase64 = fields.String(required=True, allow_none=False)


class PmsOcrCheckinResult(Datamodel):
    _name = "pms.ocr.checkin.result"
    nationality = fields.Integer(required=False, allow_none=True)
    countryId = fields.Integer(required=False, allow_none=True)
    firstname = fields.String(required=False, allow_none=True)
    lastname = fields.String(required=False, allow_none=True)
    lastname2 = fields.String(required=False, allow_none=True)
    gender = fields.String(required=False, allow_none=True)
    birthdate = fields.String(required=False, allow_none=True)
    documentType = fields.Integer(required=False, allow_none=True)
    documentExpeditionDate = fields.String(required=False, allow_none=True)
    documentSupportNumber = fields.String(required=False, allow_none=True)
    documentNumber = fields.String(required=False, allow_none=True)
    residenceStreet = fields.String(required=False, allow_none=True)
    residenceCity = fields.String(required=False, allow_none=True)
    countryState = fields.Integer(required=False, allow_none=True)
