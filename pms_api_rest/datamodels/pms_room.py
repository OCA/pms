from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsRoomSearchParam(Datamodel):
    _name = "pms.room.search.param"
    name = fields.String(required=False, allow_none=False)
    pmsPropertyId = fields.Integer(required=True, allow_none=False)
    availabilityFrom = fields.String(required=False, allow_none=False)
    availabilityTo = fields.String(required=False, allow_none=False)
    currentLines = fields.List(fields.Integer(), required=False, allow_none=False)
    pricelistId = fields.Integer(required=False, allow_none=False)


class PmsRoomInfo(Datamodel):
    _name = "pms.room.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    roomTypeId = fields.Integer(required=False, allow_none=True)
    capacity = fields.Integer(required=False, allow_none=True)
    shortName = fields.String(required=False, allow_none=True)
    roomTypeClassId = fields.Integer(required=False, allow_none=True)
    ubicationId = fields.Integer(required=False, allow_none=True)
    extraBedsAllowed = fields.Integer(required=False, allow_none=True)
    roomAmenityIds = fields.List(fields.Integer(), required=False)
