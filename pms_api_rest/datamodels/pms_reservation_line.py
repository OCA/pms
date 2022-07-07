from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsReservationLineSearchParam(Datamodel):
    _name = "pms.reservation.line.search.param"
    date = fields.String(required=False, allow_none=False)
    reservationId = fields.Integer(required=False, allow_none=False)
    pmsPropertyId = fields.Integer(required=False, allow_none=False)
    roomId = fields.Integer(required=False, allow_none=False)
    overbooking = fields.Boolean(required=False, allow_none=False)


class PmsReservationLineInfo(Datamodel):
    _name = "pms.reservation.line.info"
    id = fields.Integer(required=False, allow_none=False)
    date = fields.String(required=False, allow_none=False)
    price = fields.Float(required=False, allow_none=False)
    discount = fields.Float(required=False, allow_none=False)
    cancelDiscount = fields.Float(required=False, allow_none=False)
    roomId = fields.Integer(required=False, allow_none=False)
    reservationId = fields.Integer(required=False, allow_none=False)
    pmsPropertyId = fields.Integer(required=False, allow_none=False)
