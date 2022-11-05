from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class PmsTransactionSearchParam(Datamodel):
    _name = "pms.transaction.search.param"
    _inherit = "pms.rest.metadata"
    pmsPropertyId = fields.Integer(required=True, allow_none=False)
    filter = fields.String(required=False, allow_none=True)
    dateStart = fields.String(required=False, allow_none=True)
    dateEnd = fields.String(required=False, allow_none=True)
    transactionMethodId = fields.Integer(required=False, allow_none=True)
    transactionType = fields.String(required=False, allow_none=True)
    # REVIEW: Fields to avoid?:


class PmsTransactionsResults(Datamodel):
    _name = "pms.transaction.results"
    transactions = fields.List(NestedModel("pms.transaction.info"))
    total = fields.Float(required=False, allow_none=True)
    totalTransactions = fields.Integer(required=False, allow_none=True)


class PmsTransactionInfo(Datamodel):
    _name = "pms.transaction.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    date = fields.String(required=False, allow_none=True)
    journalId = fields.Integer(required=False, allow_none=True)
    amount = fields.Float(required=False, allow_none=True)
    partnerId = fields.Integer(required=False, allow_none=True)
    reservationIds = fields.List(fields.Integer(), required=False)
    folioId = fields.Integer(required=False, allow_none=True)
    destinationJournalId = fields.Integer(required=False, allow_none=True)
    reference = fields.String(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=False, allow_none=True)
    createUid = fields.Integer(required=False, allow_none=True)
    transactionType = fields.String(required=False, allow_none=True)
    # REVIEW: Fields to avoid?:
    partnerName = fields.String(required=False, allow_none=True)
