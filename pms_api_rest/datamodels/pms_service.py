from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsServiceInfo(Datamodel):
    _name = "pms.service.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    quantity = fields.Integer(required=False, allow_none=True)
    priceTotal = fields.Float(required=False, allow_none=True)
    priceSubtotal = fields.Float(required=False, allow_none=True)
    priceTaxes = fields.Float(required=False, allow_none=True)
    discount = fields.Float(required=False, allow_none=True)
