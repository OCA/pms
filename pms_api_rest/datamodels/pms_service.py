from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class PmsServiceInfo(Datamodel):
    _name = "pms.service.info"
    id = fields.Integer(required=False, allow_none=True)
    reservationId = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    productId = fields.Integer(required=False, allow_none=True)
    quantity = fields.Integer(required=False, allow_none=True)
    priceTotal = fields.Float(required=False, allow_none=True)
    priceSubtotal = fields.Float(required=False, allow_none=True)
    priceTaxes = fields.Float(required=False, allow_none=True)
    discount = fields.Float(required=False, allow_none=True)
    isBoardService = fields.Boolean(required=False, allow_none=True)
    serviceLines = fields.List(NestedModel("pms.service.line.info"))
    priceUnit = fields.Float(required=False, allow_none=True)
    isCancelPenalty = fields.Boolean(required=False, allow_none=True)
    boardServiceLineId = fields.Integer(required=False, allow_none=True)
