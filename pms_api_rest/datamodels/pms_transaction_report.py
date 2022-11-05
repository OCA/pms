from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsTransactionReportSearchParam(Datamodel):
    _name = "pms.transaction.report.search.param"
    dateFrom = fields.String(required=False, allow_none=True)
    dateTo = fields.String(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=False, allow_none=True)


class PmsTransactionReportInput(Datamodel):
    _name = "pms.transaction.report"
    fileName = fields.String(required=False, allow_none=True)
    binary = fields.String(required=False, allow_none=True)
