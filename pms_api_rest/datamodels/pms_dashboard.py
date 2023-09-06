from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsDashboardSearchParam(Datamodel):
    _name = "pms.dashboard.search.param"
    date = fields.String(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=False, allow_none=True)


class PmsDashboardRangeDatesSearchParam(Datamodel):
    _name = "pms.dashboard.range.dates.search.param"
    dateFrom = fields.String(required=False, allow_none=True)
    dateTo = fields.String(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=False, allow_none=True)



class PmsDashboardPendingReservations(Datamodel):
    _name = "pms.dashboard.pending.reservations"
    date = fields.String(required=False, allow_none=True)
    pendingArrivalReservations = fields.Integer(required=False, allow_none=True)
    completedArrivalReservations = fields.Integer(required=False, allow_none=True)
    pendingDepartureReservations = fields.Integer(required=False, allow_none=True)
    completedDepartureReservations = fields.Integer(required=False, allow_none=True)



class PmsDashboardNumericResponse(Datamodel):
    _name = "pms.dashboard.numeric.response"
    value = fields.Float(required=False, allow_none=True)
