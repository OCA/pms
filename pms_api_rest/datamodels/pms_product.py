from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsProductSearchParam(Datamodel):
    _name = "pms.product.search.param"
    name = fields.String(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=True, allow_none=False)


class PmProductInfo(Datamodel):
    _name = "pms.product.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    perDay = fields.Boolean(required=False, allow_none=True)
    perPerson = fields.Boolean(required=False, allow_none=True)
    consumedOn = fields.String(required=False, allow_none=True)
