from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsReservationLineSearchParam(Datamodel):
    _name = "pms.reservation.line.search.param"
    date = fields.String(required=False, allow_none=False)
    dateFrom = fields.String(required=False, allow_none=False)
    dateTo = fields.String(required=False, allow_none=False)
    reservationId = fields.Integer(required=False, allow_none=False)
    pmsPropertyId = fields.Integer(required=False, allow_none=False)
    roomId = fields.Integer(required=False, allow_none=False)
    overbooking = fields.Boolean(required=False, allow_none=False)


class PmsReservationLineInfo(Datamodel):
    _name = "pms.reservation.line.info"
    id = fields.Integer(required=False, allow_none=True)
    date = fields.String(required=False, allow_none=True)
    price = fields.Float(required=False, allow_none=True)
    discount = fields.Float(required=False, allow_none=True)
    cancelDiscount = fields.Float(required=False, allow_none=True)
    roomId = fields.Integer(required=False, allow_none=True)
    reservationId = fields.Integer(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=False, allow_none=True)
    isReselling = fields.Boolean(required=False, allow_none=True)
    reservationType = fields.String(required=False, allow_none=True)
    state = fields.String(required=False, allow_none=True)
    isSplitted = fields.Boolean(required=False, allow_none=True)
