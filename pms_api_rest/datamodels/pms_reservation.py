from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsReservationInfo(Datamodel):
    _name = "pms.reservation.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    folioId = fields.Integer(required=False, allow_none=True)
    folioSequence = fields.Integer(required=False, allow_none=True)
    partnerName = fields.String(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=False, allow_none=True)
    boardServiceId = fields.Integer(required=False, allow_none=True)
    saleChannelId = fields.Integer(required=False, allow_none=True)
    agencyId = fields.Integer(required=False, allow_none=True)

    checkin = fields.String(required=False, allow_none=True)
    checkout = fields.String(required=False, allow_none=True)
    arrivalHour = fields.String(required=False, allow_none=True)
    departureHour = fields.String(required=False, allow_none=True)
    roomTypeId = fields.Integer(required=False, allow_none=True)
    preferredRoomId = fields.Integer(required=False, allow_none=True)
    pricelistId = fields.Integer(required=False, allow_none=True)

    adults = fields.Integer(required=False, allow_none=True)
    overbooking = fields.Boolean(required=False, allow_none=True)
    externalReference = fields.String(required=False, allow_none=True)
    state = fields.String(required=False, allow_none=True)
    children = fields.Integer(required=False, allow_none=True)
    readyForCheckin = fields.Boolean(required=False, allow_none=True)
    allowedCheckout = fields.Boolean(required=False, allow_none=True)
    isSplitted = fields.Boolean(required=False, allow_none=True)
    pendingCheckinData = fields.Integer(required=False, allow_none=True)
    createDate = fields.String(required=False, allow_none=True)
    segmentationId = fields.Integer(required=False, allow_none=True)
    cancellationPolicyId = fields.Integer(required=False, allow_none=True)
    toAssign = fields.Boolean(required=False, allow_none=True)
    reservationType = fields.String(required=False, allow_none=True)

    priceTotal = fields.Float(required=False, allow_none=True)
    discount = fields.Float(required=False, allow_none=True)
    commissionAmount = fields.Float(required=False, allow_none=True)
    commissionPercent = fields.Float(required=False, allow_none=True)
    priceOnlyServices = fields.Float(required=False, allow_none=True)
    priceOnlyRoom = fields.Float(required=False, allow_none=True)
    pendingAmount = fields.Float(required=False, allow_none=True)

    # TODO: Refact
    # services = fields.List(fields.Dict(required=False, allow_none=True))
    # messages = fields.List(fields.Dict(required=False, allow_none=True))
