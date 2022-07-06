from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsAvailabilityPlanRuleSearchParam(Datamodel):
    _name = "pms.availability.plan.rule.search.param"
    dateFrom = fields.String(required=True, allow_none=False)
    dateTo = fields.String(required=True, allow_none=False)
    pmsPropertyId = fields.Integer(required=True, allow_none=False)


class PmsAvailabilityPlanRuleInfo(Datamodel):
    _name = "pms.availability.plan.rule.info"
    availabilityRuleId = fields.Integer(required=False, allow_none=True)
    minStay = fields.Integer(required=False, allow_none=True)
    minStayArrival = fields.Integer(required=False, allow_none=True)
    maxStay = fields.Integer(required=False, allow_none=True)
    maxStayArrival = fields.Integer(required=False, allow_none=True)
    closed = fields.Boolean(required=False, allow_none=True)
    closedDeparture = fields.Boolean(required=False, allow_none=True)
    closedArrival = fields.Boolean(required=False, allow_none=True)
    roomTypeId = fields.Integer(required=False, allow_none=True)
    date = fields.String(required=False, allow_none=True)
    quota = fields.Integer(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=False, allow_none=True)
