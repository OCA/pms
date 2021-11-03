from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsReservationShortInfo(Datamodel):
    _name = "pms.reservation.short.info"
    id = fields.Integer(required=False, allow_none=True)
    price = fields.Float(required=False, allow_none=True)
    checkin = fields.String(required=False, allow_none=True)
    checkout = fields.String(required=False, allow_none=True)
