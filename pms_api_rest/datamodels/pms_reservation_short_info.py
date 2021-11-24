from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsReservationShortInfo(Datamodel):
    _name = "pms.reservation.short.info"
    id = fields.Integer(required=False, allow_none=True)
<<<<<<< HEAD
    price = fields.Float(required=False, allow_none=True)
    checkin = fields.String(required=False, allow_none=True)
    checkout = fields.String(required=False, allow_none=True)
=======
    partner = fields.String(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    checkin = fields.String(required=False, allow_none=True)
    checkout = fields.String(required=False, allow_none=True)
    roomTypeId = fields.String(required=False, allow_none=True)
    preferredRoomId = fields.String(required=False, allow_none=True)
    priceTotal = fields.Float(required=False, allow_none=True)
    priceOnlyServices = fields.Float(required=False, allow_none=True)
    priceOnlyRoom = fields.Float(required=False, allow_none=True)
    pricelist = fields.String(required=False, allow_none=True)
    services = fields.List(fields.Dict(required=False, allow_none=True))
    messages = fields.List(fields.Dict(required=False, allow_none=True))
>>>>>>> d6e6a667... [IMP] pms_api_rest: add get_reservation and get_checkin_partners
