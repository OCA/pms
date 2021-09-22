from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsCalendarShortInfo(Datamodel):
    _name = "pms.calendar.short.info"
    id = fields.Integer(required=False, allow_none=True)
    date = fields.String(required=False, allow_none=True)
    roomId = fields.Integer(required=False, allow_none=True)
    partnerId = fields.Integer(required=False, allow_none=True)
    reservationId = fields.Integer(required=False, allow_none=True)
