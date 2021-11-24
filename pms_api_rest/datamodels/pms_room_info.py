from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsRoomInfo(Datamodel):
    _name = "pms.room.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
