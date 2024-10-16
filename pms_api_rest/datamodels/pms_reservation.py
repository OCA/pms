from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class PmsReservationShortInfo(Datamodel):
    _name = "pms.reservation.short.info"
    id = fields.Integer(required=False, allow_none=True)
    boardServiceId = fields.Integer(required=False, allow_none=True)
    checkin = fields.String(required=False, allow_none=True)
    checkout = fields.String(required=False, allow_none=True)
    roomTypeId = fields.Integer(required=False, allow_none=True)
    roomTypeClassId = fields.Integer(required=False, allow_none=True)
    preferredRoomId = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    adults = fields.Integer(required=False, allow_none=True)
    stateCode = fields.String(required=False, allow_none=True)
    stateDescription = fields.String(required=False, allow_none=True)
    children = fields.Integer(required=False, allow_none=True)
    paymentState = fields.String(required=False, allow_none=True)
    readyForCheckin = fields.Boolean(required=False, allow_none=True)
    allowedCheckout = fields.Boolean(required=False, allow_none=True)
    isSplitted = fields.Boolean(required=False, allow_none=True)
    priceTotal = fields.Float(required=False, allow_none=True)
    servicesCount = fields.Integer(required=False, allow_none=True)
    folioSequence = fields.Integer(required=False, allow_none=True)
    pricelistId = fields.Integer(required=False, allow_none=True)
    nights = fields.Integer(required=False, allow_none=True)
    numServices = fields.Integer(required=False, allow_none=True)
    toAssign = fields.Boolean(required=False, allow_none=True)
    overbooking = fields.Boolean(required=False, allow_none=True)


class PmsReservationInfo(Datamodel):
    _name = "pms.reservation.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    folioId = fields.Integer(required=False, allow_none=True)
    folioSequence = fields.Integer(required=False, allow_none=True)
    partnerName = fields.String(required=False, allow_none=True)
    boardServiceId = fields.Integer(required=False, allow_none=True)
    boardServices = fields.List(
        NestedModel("pms.service.info"), required=False, allow_none=True
    )
    saleChannelId = fields.Integer(required=False, allow_none=True)
    agencyId = fields.Integer(required=False, allow_none=True)
    userId = fields.Integer(required=False, allow_none=True)

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
    stateCode = fields.String(required=False, allow_none=True)
    stateDescription = fields.String(required=False, allow_none=True)
    children = fields.Integer(required=False, allow_none=True)
    readyForCheckin = fields.Boolean(required=False, allow_none=True)
    checkinPartnerCount = fields.Integer(required=False, allow_none=True)
    allowedCheckout = fields.Boolean(required=False, allow_none=True)
    isSplitted = fields.Boolean(required=False, allow_none=True)
    pendingCheckinData = fields.Integer(required=False, allow_none=True)
    createDate = fields.String(required=False, allow_none=True)
    segmentationId = fields.Integer(required=False, allow_none=True)
    cancelationRuleId = fields.Integer(required=False, allow_none=True)
    toAssign = fields.Boolean(required=False, allow_none=True)
    toCheckout = fields.Boolean(required=False, allow_none=True)
    reservationType = fields.String(required=False, allow_none=True)

    priceTotal = fields.Float(required=False, allow_none=True)
    priceTax = fields.Float(required=False, allow_none=True)
    discount = fields.Float(required=False, allow_none=True)
    servicesDiscount = fields.Float(required=False, allow_none=True)
    commissionAmount = fields.Float(required=False, allow_none=True)
    commissionPercent = fields.Float(required=False, allow_none=True)
    priceOnlyServices = fields.Float(required=False, allow_none=True)
    priceOnlyRoom = fields.Float(required=False, allow_none=True)
    nights = fields.Integer(required=False, allow_none=True)
    numServices = fields.Integer(required=False, allow_none=True)

    reservationLines = fields.List(NestedModel("pms.reservation.line.info"))
    services = fields.List(
        NestedModel("pms.service.info"), required=False, allow_none=True
    )
    partnerRequests = fields.String(required=False, allow_none=True)
    nights = fields.Integer(required=False, allow_none=True)
    isReselling = fields.Boolean(required=False, allow_none=True)
    createdBy = fields.String(required=False, allow_none=True)

    # TODO: Refact
    # messages = fields.List(fields.Dict(required=False, allow_none=True))
