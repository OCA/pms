from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsAmenitySearchParam(Datamodel):
    _name = "pms.amenity.search.param"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=True, allow_none=False)


class PmsAmenityInfo(Datamodel):
    _name = "pms.amenity.info"
    id = fields.Integer(required=True, allow_none=False)
    name = fields.String(required=True, allow_none=False)
    amenityTypeId = fields.Integer(required=True, allow_none=False)
