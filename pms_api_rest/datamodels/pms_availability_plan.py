from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsAvailabilityPlanInfo(Datamodel):
    _name = "pms.availability.plan.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    pmsPropertyIds = fields.List(fields.Integer(required=False, allow_none=True))
