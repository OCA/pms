from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsServiceLineInfo(Datamodel):
    _name = "pms.service.line.info"
    id = fields.Integer(required=False, allow_none=True)
    date = fields.String(required=False, allow_none=True)
    priceUnit = fields.Float(required=False, allow_none=True)
    discount = fields.Float(required=False, allow_none=True)
    quantity = fields.Integer(required=False, allow_none=True)
