from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class PmsPaymentInfo(Datamodel):
    _name = "pms.payment.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    amount = fields.Float(required=False, allow_none=True)
    journalId = fields.Integer(required=False, allow_none=True)
    date = fields.String(required=False, allow_none=True)
    partnerName = fields.String(required=False, allow_none=True)
    partnerId = fields.Integer(required=False, allow_none=True)
    paymentType = fields.String(required=False, allow_none=True)
    partnerType = fields.String(required=False, allow_none=True)
    isTransfer = fields.Boolean(required=False, allow_none=True)
    reference = fields.String(required=False, allow_none=True)
    createUid = fields.Integer(required=False, allow_none=True)


class PmsPaymentSearchParam(Datamodel):
    _name = "pms.payment.search.param"
    _inherit = "pms.rest.metadata"
    pmsPropertyId = fields.Integer(required=True, allow_none=False)
    filter = fields.String(required=False, allow_none=True)
    dateStart = fields.String(required=False, allow_none=True)
    dateEnd = fields.String(required=False, allow_none=True)
    paymentMethodId = fields.Integer(required=False, allow_none=True)
    # TODO: paymentTypes filter
    paymentTypes = fields.List(fields.Integer(required=False, allow_none=True))
    paymentType = fields.String(required=False, allow_none=True)
    partnerType = fields.String(required=False, allow_none=True)
    isTransfer = fields.Boolean(required=False, allow_none=True)


class PmsPaymentResults(Datamodel):
    _name = "pms.payment.results"
    payments = fields.List(NestedModel("pms.payment.info"))
    total = fields.Float(required=False, allow_none=True)
    totalPayments = fields.Integer(required=False, allow_none=True)


class PmsTransactionInfo(Datamodel):
    _name = "pms.transaction.info"
    id = fields.Integer(required=False, allow_none=True)
    date = fields.String(required=False, allow_none=True)
    journalId = fields.Integer(required=False, allow_none=True)
    amount = fields.Float(required=False, allow_none=True)
    partnerId = fields.Integer(required=False, allow_none=True)
    reservationIds = fields.List(fields.Integer(), required=False)
    folioId = fields.Integer(required=False, allow_none=True)

    transactionType = fields.String(required=False, allow_none=True)
    destinationJournalId = fields.Integer(required=False, allow_none=True)
    reference = fields.String(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=False, allow_none=True)
    createUid = fields.Integer(required=False, allow_none=True)
