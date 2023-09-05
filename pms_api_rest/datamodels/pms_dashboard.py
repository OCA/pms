from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsDashboardPendingReservationsSearchParam(Datamodel):
    _name = "pms.dashboard.pending.reservations.search.param"
    date = fields.String(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=False, allow_none=True)


class PmsDashboardPendingReservations(Datamodel):
    _name = "pms.dashboard.pending.reservations"
    pendingReservations = fields.Integer(required=False, allow_none=True)
    completedReservations = fields.Integer(required=False, allow_none=True)


