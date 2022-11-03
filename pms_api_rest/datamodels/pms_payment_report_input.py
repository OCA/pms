from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class PmsPaymentReportSearchParam(Datamodel):
    _name = "pms.payment.report.search.param"
    dateFrom = fields.String(required=False, allow_none=True)
    dateTo = fields.String(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=False, allow_none=True)


class PmsPaymentReportInput(Datamodel):
    _name = "pms.payment.report"
    fileName = fields.String(required=False, allow_none=True)
    binary = fields.String(required=False, allow_none=True)
