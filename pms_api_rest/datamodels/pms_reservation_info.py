from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsReservationInfo(Datamodel):
    _name = "pms.reservation.info"
    id = fields.Integer(required=False, allow_none=True)
    partner = fields.String(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    checkin = fields.String(required=False, allow_none=True)
    checkout = fields.String(required=False, allow_none=True)
    roomTypeId = fields.Integer(required=False, allow_none=True)
    roomTypeName = fields.String(required=False, allow_none=True)
    preferredRoomId = fields.String(required=False, allow_none=True)
    priceTotal = fields.Float(required=False, allow_none=True)
    priceOnlyServices = fields.Float(required=False, allow_none=True)
    priceOnlyRoom = fields.Float(required=False, allow_none=True)
    pricelistName = fields.String(required=False, allow_none=True)
    pricelistId = fields.Integer(required=False, allow_none=True)
    services = fields.List(fields.Dict(required=False, allow_none=True))
    messages = fields.List(fields.Dict(required=False, allow_none=True))
    property = fields.Integer(required=False, allow_none=True)
    boardServiceId = fields.Integer(required=False, allow_none=True)
    channelTypeId = fields.Integer(required=False, allow_none=True)
