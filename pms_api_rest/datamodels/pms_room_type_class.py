from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsRoomTypeClassSearchParam(Datamodel):
    _name = "pms.room.type.class.search.param"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    pms_property_ids = fields.List(fields.Integer(), required=False)


class PmsRoomTypeClassInfo(Datamodel):
    _name = "pms.room.type.class.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    pms_property_ids = fields.List(fields.Integer(), required=False)
