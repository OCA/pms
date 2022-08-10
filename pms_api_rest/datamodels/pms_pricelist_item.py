from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class PmsPricelistItemSearchParam(Datamodel):
    _name = "pms.pricelist.item.search.param"
    dateFrom = fields.String(required=True, allow_none=False)
    dateTo = fields.String(required=True, allow_none=False)
    pmsPropertyId = fields.Integer(required=True, allow_none=False)


class PmsPricelistItemInfo(Datamodel):
    _name = "pms.pricelist.item.info"
    pricelistItemId = fields.Integer(required=False, allow_none=True)
    price = fields.Float(required=False, allow_none=True)
    roomTypeId = fields.Integer(required=False, allow_none=True)
    date = fields.String(required=False, allow_none=True)
    pricelistId = fields.Integer(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=False, allow_none=True)

class PmsPricelistItemsInfo(Datamodel):
    _name = "pms.pricelist.items.info"
    pricelistItems = fields.List(NestedModel("pms.pricelist.item.info"))
