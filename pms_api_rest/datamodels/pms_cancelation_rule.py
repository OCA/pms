from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsCancelationRuleSearchParam(Datamodel):
    _name = "pms.cancelation.rule.search.param"
    pricelistId = fields.Integer(required=False, allow_none=True)
    pmsPropertyId = fields.String(required=False, allow_none=True)


class PmsCancelationRuleInfo(Datamodel):
    _name = "pms.cancelation.rule.info"
    id = fields.Integer(required=True, allow_none=False)
    name = fields.String(required=True, allow_none=False)
