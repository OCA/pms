from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsExtraBedSearchParam(Datamodel):
    _name = "pms.extra.beds.search.param"
    name = fields.String(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=True, allow_none=False)
    dateFrom = fields.String(required=False, allow_none=True)
    dateTo = fields.String(required=False, allow_none=True)


class PmsExtraBedInfo(Datamodel):
    _name = "pms.extra.bed.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    dailyLimitConfig = fields.Integer(required=False, allow_none=True)
    dailyLimitAvail = fields.Integer(required=False, allow_none=True)
