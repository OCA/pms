from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsDashboardCheckinsSearchParam(Datamodel):
    _name = "pms.dashboard.checkins.search.param"
    dateTo = fields.String(required=False, allow_none=True)
    dateFrom = fields.String(required=False, allow_none=True)


class PmsDashboardCheckins(Datamodel):
    _name = "pms.dashboard.checkins"
    id = fields.Integer(required=True, allow_none=False)
    checkinPartnerState = fields.String(required=False, allow_none=True)
    date = fields.String(required=False, allow_none=True)


