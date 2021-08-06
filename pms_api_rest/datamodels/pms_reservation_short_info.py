from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsReservationShortInfo(Datamodel):
    _name = "pms.reservation.short.info"

    id = fields.Integer(required=True, allow_none=False)
    partner = fields.String(required=True, allow_none=False)
    checkin = fields.String(required=True, allow_none=False)
    checkout = fields.String(required=True, allow_none=False)
    preferredRoomId = fields.String(required=True, allow_none=False)
    roomTypeId = fields.String(required=True, allow_none=False)
    name = fields.String(required=True, allow_none=False)
    partnerRequests = fields.String(required=False, allow_none=True)
    state = fields.String(required=True, allow_none=False)
    priceTotal = fields.Float(required=True, allow_none=True)
    adults = fields.Integer(required=True, allow_none=False)
    channelTypeId = fields.String(required=False, allow_none=True)
    agencyId = fields.String(required=False, allow_none=True)
    boardServiceId = fields.String(required=False, allow_none=True)
    checkinsRatio = fields.Float(required=True, allow_none=False)
    outstanding = fields.Float(required=True, allow_none=False)
    pwaActionButtons = fields.Dict(required=True, allow_none=False)
