from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsAmenityTypeSearchParam(Datamodel):
    _name = "pms.amenity.type.search.param"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=True, allow_none=False)


class PmsAmenityTypeInfo(Datamodel):
    _name = "pms.amenity.type.info"
    id = fields.Integer(required=True, allow_none=False)
    name = fields.String(required=True, allow_none=False)
