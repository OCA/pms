from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsReservationLineSearchParam(Datamodel):
    _name = "pms.reservation.line.search.param"
    id = fields.Integer(required=False, allow_none=True)
    date = fields.String(required=False, allow_none=True)
    reservationId = fields.Integer(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=False, allow_none=True)


class PmsReservationLineInfo(Datamodel):
    _name = "pms.reservation.line.info"
    id = fields.Integer(required=False, allow_none=False)
    date = fields.String(required=False, allow_none=False)
    price = fields.Float(required=False, allow_none=False)
    discount = fields.Float(required=False, allow_none=True)
    cancelDiscount = fields.Float(required=False, allow_none=True)
    roomId = fields.Integer(required=False, allow_none=False)
    reservationId = fields.Integer(required=False, allow_none=False)
    pmsPropertyId = fields.Integer(required=False, allow_none=False)
