from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsDashboardPendingReservationsSearchParam(Datamodel):
    _name = "pms.dashboard.pending.reservations.search.param"
    dateTo = fields.String(required=False, allow_none=True)
    dateFrom = fields.String(required=False, allow_none=True)


class PmsDashboardPendingReservations(Datamodel):
    _name = "pms.dashboard.pending.reservations"
    id = fields.Integer(required=True, allow_none=False)
    state = fields.String(required=False, allow_none=True)
    reservationType = fields.String(required=False, allow_none=True)
    checkin = fields.String(required=False, allow_none=True)


