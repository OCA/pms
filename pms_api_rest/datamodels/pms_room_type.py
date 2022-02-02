from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsRoomTypeSearchParam(Datamodel):
    _name = "pms.room.type.search.param"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    pms_property_ids = fields.List(fields.Integer(), required=False)


class PmsRoomTypeInfo(Datamodel):
    _name = "pms.room.type.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    pms_property_ids = fields.List(fields.Integer(), required=False)
