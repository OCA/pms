from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsCalendarSwapInfo(Datamodel):
    _name = "pms.calendar.swap.info"
    swapFrom = fields.String(required=True, allow_none=False)
    swapTo = fields.String(required=True, allow_none=False)
    roomIdA = fields.Integer(required=True, allow_none=False)
    roomIdB = fields.Integer(required=True, allow_none=False)
