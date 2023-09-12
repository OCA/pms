from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class CivitfunCheckinPartnerInfo(Datamodel):
    _name = "civitfun.checkin.partner.info"

    idCheckinGuest = fields.String(required=False, allow_none=True)
    id = fields.String(required=False, allow_none=True)
    position = fields.Integer(required=False, allow_none=True)
    email = fields.String(required=False, allow_none=True)
    lang = fields.String(required=False, allow_none=True)
    language = fields.String(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    surname = fields.String(required=False, allow_none=True)
    secondSurname = fields.String(required=False, allow_none=True)
    gender = fields.String(required=False, allow_none=True)
    birthdate = fields.Date(required=False, allow_none=True)
    nationality = fields.String(required=False, allow_none=True)
    documentType = fields.String(required=False, allow_none=True)
    documentNumber = fields.String(required=False, allow_none=True)
    expeditionDate = fields.Date(required=False, allow_none=True)
    expirationDate = fields.Date(required=False, allow_none=True)
    assignedRoom = fields.Dict(required=False, allow_none=True)
    customFields = fields.Dict(required=False, allow_none=True)
    legalFields = fields.Dict(required=False, allow_none=True)
    birthDate = fields.Date(required=False, allow_none=True)
    files = fields.List(fields.Dict(), required=False, allow_none=True)


class CivitfunGuestMeta(Datamodel):
    _name = "civitfun.guest.meta"

    propertyId = fields.String(required=False, allow_none=True)
    bookingIdentifier = fields.String(required=False, allow_none=True)
    guests = fields.List(NestedModel("civitfun.checkin.partner.info"))


class CivitfunGuestMetaResult(Datamodel):
    _name = "civitfun.guest.meta.result"

    success = fields.Boolean(required=False, allow_none=True)
    message = fields.String(required=False, allow_none=True)
    guestIds = fields.List(fields.Dict(required=False, allow_none=True))
