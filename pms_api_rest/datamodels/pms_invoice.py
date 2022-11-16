from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class PmsAccountInvoiceInfo(Datamodel):
    _name = "pms.invoice.info"
    id = fields.Integer(required=False, allow_none=True)
    amount = fields.Float(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    date = fields.String(required=False, allow_none=True)
    paymentState = fields.String(required=False, allow_none=True)
    state = fields.String(required=False, allow_none=True)
    # REVIEW: partnerName??, is not enought partnerId?
    partnerName = fields.String(required=False, allow_none=True)
    partnerId = fields.Integer(required=False, allow_none=True)
    moveLines = fields.List(NestedModel("pms.invoice.line.info"))
    saleLines = fields.List(NestedModel("pms.folio.sale.line.info"))
    narration = fields.String(required=False, allow_none=True)
    portalUrl = fields.String(required=False, allow_none=True)
    moveType = fields.String(required=False, allow_none=True)
    isReversed = fields.Boolean(required=False, allow_none=True)
    isDownPaymentInvoice = fields.Boolean(required=False, allow_none=True)
    isSimplifiedInvoice = fields.Boolean(required=False, allow_none=True)
    reversedEntryId = fields.Integer(required=False, allow_none=True)
    # REVIEW: originDownPaymentId Only input field to service to
    # create downpayment invoices from payments
    originDownPaymentId = fields.Integer(required=False, allow_none=True)
