from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsReservationUpdates(Datamodel):
    _name = "pms.reservation.updates"
    reservationLinesChanges = fields.List(fields.Dict(required=False, allow_none=True))
    preferredRoomId = fields.Integer(required=False, allow_none=True)
    boardServiceId = fields.Integer(required=False, allow_none=True)
    pricelistId = fields.Integer(required=False, allow_none=True)


class PmsCalendarSwapInfo(Datamodel):
    _name = "pms.calendar.swap.info"
    swapFrom = fields.String(required=True, allow_none=False)
    swapTo = fields.String(required=True, allow_none=False)
    roomIdA = fields.Integer(required=True, allow_none=False)
    roomIdB = fields.Integer(required=True, allow_none=False)
    pms_property_id = fields.Integer(required=False, allow_none=True)


class PmsCalendarSearchParam(Datamodel):
    _name = "pms.calendar.search.param"
    date_from = fields.String(required=False, allow_none=True)
    date_to = fields.String(required=False, allow_none=True)
    pms_property_id = fields.Integer(required=True, allow_none=False)
    pricelist_id = fields.Integer(required=False, allow_none=True)


class PmsCalendarFreeDailyRoomsByType(Datamodel):
    _name = "pms.calendar.free.daily.rooms.by.type"
    date = fields.String(required=True, allow_none=False)
    roomTypeId = fields.Integer(required=True, allow_none=False)
    freeRooms = fields.Integer(required=True, allow_none=False)


class PmsCalendarDailyInvoicing(Datamodel):
    _name = "pms.calendar.daily.invoicing"
    date = fields.String(required=True, allow_none=False)
    invoicingTotal = fields.Float(required=True, allow_none=False)


class PmsCalendarInfo(Datamodel):
    _name = "pms.calendar.info"
    id = fields.Integer(required=False, allow_none=True)
    state = fields.String(required=False, allow_none=True)
    date = fields.String(required=False, allow_none=True)
    roomId = fields.Integer(required=False, allow_none=True)
    roomTypeName = fields.String(required=False, allow_none=True)
    toAssign = fields.Boolean(required=False, allow_none=True)
    splitted = fields.Boolean(required=False, allow_none=True)
    partnerId = fields.Integer(required=False, allow_none=True)
    partnerName = fields.String(required=False, allow_none=True)
    folioId = fields.Integer(required=False, allow_none=True)
    reservationId = fields.Integer(required=False, allow_none=True)
    reservationName = fields.String(required=False, allow_none=True)
    reservationType = fields.String(required=False, allow_none=True)
    isFirstNight = fields.Boolean(required=False, allow_none=True)
    isLastNight = fields.Boolean(required=False, allow_none=True)
    totalPrice = fields.Float(required=False, allow_none=True)
    pendingPayment = fields.Float(required=False, allow_none=True)
    numNotifications = fields.Integer(required=False, allow_none=True)
    adults = fields.Integer(required=False, allow_none=True)
    hasNextLine = fields.Boolean(required=False, allow_none=True)
    nextLineSplitted = fields.Boolean(required=False, allow_none=True)
    previousLineSplitted = fields.Boolean(required=False, allow_none=True)
    closureReason = fields.String(required=False, allow_none=True)


class PmsCalendarAlertsPerDay(Datamodel):
    _name = "pms.calendar.alerts.per.day"
    date = fields.String(required=True, allow_none=False)
    overbooking = fields.Boolean(required=True, allow_none=False)
