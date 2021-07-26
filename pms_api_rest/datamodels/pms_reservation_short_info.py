from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsReservationShortInfo(Datamodel):
    _name = "pms.reservation.short.info"

    id = fields.Integer(required=True, allow_none=False)
    partner = fields.String(required=True, allow_none=False)
    checkin = fields.String(required=True, allow_none=False)
    checkout = fields.String(required=True, allow_none=False)
    preferred_room_id = fields.String(required=True, allow_none=False)
    room_type_id = fields.String(required=True, allow_none=False)
    name = fields.String(required=True, allow_none=False)
    partner_requests = fields.String(required=False, allow_none=True)
