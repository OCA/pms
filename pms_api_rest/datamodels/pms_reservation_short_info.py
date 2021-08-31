from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsReservationShortInfo(Datamodel):
    _name = "pms.reservation.short.info"

    id = fields.Integer(required=True, allow_none=False)
    partner = fields.String(required=False, allow_none=True)
    checkin = fields.String(required=True, allow_none=True)
    checkout = fields.String(required=True, allow_none=True)
    preferredRoomId = fields.String(required=False, allow_none=True)
    roomTypeId = fields.String(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    partnerRequests = fields.String(required=False, allow_none=True)
    state = fields.String(required=False, allow_none=True)
    priceTotal = fields.Float(required=False, allow_none=True)
    adults = fields.Integer(required=False, allow_none=True)
    channelTypeId = fields.String(required=False, allow_none=True)
    agencyId = fields.String(required=False, allow_none=True)
    boardServiceId = fields.String(required=False, allow_none=True)
    checkinsRatio = fields.Float(required=False, allow_none=True)
    outstanding = fields.Float(required=False, allow_none=True)
    pricelist = fields.String(required=False, allow_none=True)
    folioId = fields.Integer(required=False, allow_none=True)
    pwaActionButtons = fields.Dict(required=False, allow_none=True)
