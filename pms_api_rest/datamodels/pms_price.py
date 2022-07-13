from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsPriceSearchParam(Datamodel):
    _name = "pms.price.search.param"
    dateFrom = fields.String(required=True, allow_none=True)
    dateTo = fields.String(required=True, allow_none=True)
    pmsPropertyId = fields.Integer(required=True, allow_none=True)
    pricelistId = fields.Integer(required=True, allow_none=True)
    roomTypeId = fields.Integer(required=False, allow_none=True)
    productId = fields.Integer(required=False, allow_none=True)
    productQty = fields.Integer(required=False, allow_none=True)
    partnerId = fields.Integer(required=False, allow_none=True)


class PmsPriceInfo(Datamodel):
    _name = "pms.price.info"
    date = fields.String(required=True, allow_none=False)
    price = fields.Float(required=True, allow_none=False)
