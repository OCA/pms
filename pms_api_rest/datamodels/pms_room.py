from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsRoomSearchParam(Datamodel):
    _name = "pms.room.search.param"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    pms_property_id = fields.Integer(required=True, allow_none=False)


class PmsRoomInfo(Datamodel):
    _name = "pms.room.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    roomTypeId = fields.Integer(required=False, allow_none=True)
    capacity = fields.Integer(required=False, allow_none=True)
