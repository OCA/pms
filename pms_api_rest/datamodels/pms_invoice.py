from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class PmsAccountInvoiceInfo(Datamodel):
    _name = "pms.account.info"
    id = fields.Integer(required=False, allow_none=True)
    amount = fields.Float(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    date = fields.String(required=False, allow_none=True)
    paymentState = fields.String(required=False, allow_none=True)
    state = fields.String(required=False, allow_none=True)
    # partnerName??, is not enought partnerId?
    partnerName = fields.String(required=False, allow_none=True)
    partnerId = fields.Int(required=False, allow_none=True)
    moveLines = fields.List(NestedModel("pms.invoice.line.info"))
    saleLines = fields.List(NestedModel("pms.folio.sale.line.info"))
