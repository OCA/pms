from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsRoomClosureReasonInfo(Datamodel):
    _name = "pms.room.closure.reason.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    description = fields.String(required=False, allow_none=True)
