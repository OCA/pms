from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsProductSearchParam(Datamodel):
    _name = "pms.product.search.param"
    ids = fields.List(fields.Integer(required=False, allow_none=True))
    name = fields.String(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=True, allow_none=False)
    pricelistId = fields.Integer(required=True, allow_none=False)
    partnerId = fields.Integer(required=False, allow_none=True)
    dateConsumption = fields.String(required=False, allow_none=True)
    productQty = fields.Integer(required=False, allow_none=True)


class PmProductInfo(Datamodel):
    _name = "pms.product.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    perDay = fields.Boolean(required=False, allow_none=True)
    perPerson = fields.Boolean(required=False, allow_none=True)
    price = fields.Float(required=False, allow_none=True)
