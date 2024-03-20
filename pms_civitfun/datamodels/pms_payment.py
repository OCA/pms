from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class CivitfunPaymentSearch(Datamodel):
    _name = "civitfun.payment.search"

    propertyId = fields.String(required=False, allow_none=True)
    bookingIdentifier = fields.String(required=False, allow_none=True)
    process = fields.String(required=False, allow_none=True)
    lang = fields.String(required=False, allow_none=True)
    # guests = fields.List(NestedModel("civitfun.checkin.partner.info"))


class CivitfunPaymentInfo(Datamodel):
    _name = "civitfun.payment.info"

    success = fields.Boolean(required=False, allow_none=True)
    message = fields.String(required=False, allow_none=True)
    currency = fields.String(required=False, allow_none=True)
    accounts = fields.List(fields.Dict(required=False, allow_none=True))


class CivitfunPaymentRegister(Datamodel):
    _name = "civitfun.payment.register"

    propertyId = fields.String(required=False, allow_none=True)
    bookingIdentifier = fields.String(required=False, allow_none=True)
    process = fields.String(required=False, allow_none=True)
    paymentToken = fields.String(required=False, allow_none=True)
    paymentCard = fields.Dict(required=False, allow_none=True)
    accountIds = fields.List(fields.Dict(required=False, allow_none=True))
