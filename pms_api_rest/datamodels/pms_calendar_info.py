from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


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
    reservationId = fields.Integer(required=False, allow_none=True)
    reservationName = fields.String(required=False, allow_none=True)
    reservationType = fields.String(required=False, allow_none=True)
    isFirstDay = fields.Boolean(required=False, allow_none=True)
    isLastDay = fields.Boolean(required=False, allow_none=True)
    totalPrice = fields.Float(required=False, allow_none=True)
    pendingPayment = fields.Float(required=False, allow_none=True)
    numNotifications = fields.Integer(required=False, allow_none=True)
    adults = fields.Integer(required=False, allow_none=True)
