from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsFolioSaleInfo(Datamodel):
    _name = "pms.folio.sale.line.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    priceUnit = fields.Float(required=False, allow_none=True)
    qtyToInvoice = fields.Float(required=False, allow_none=True)
    qtyInvoiced = fields.Float(required=False, allow_none=True)
    priceTotal = fields.Float(required=False, allow_none=True)
    discount = fields.Float(required=False, allow_none=True)
    productQty = fields.Float(required=False, allow_none=True)
    reservationId = fields.Integer(required=False, allow_none=True)
    serviceId = fields.Integer(required=False, allow_none=True)
    displayType = fields.String(required=False, allow_none=True)
