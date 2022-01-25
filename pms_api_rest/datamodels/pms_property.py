from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsPropertySearchParam(Datamodel):
    _name = "pms.property.search.param"

    id = fields.Integer(required=False, allow_none=False)
    name = fields.String(required=False, allow_none=False)


class PmsPropertyInfo(Datamodel):
    _name = "pms.property.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    company = fields.String(required=False, allow_none=True)
