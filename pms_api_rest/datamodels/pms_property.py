from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsPropertySearchParam(Datamodel):
    _name = "pms.property.search.param"
    name = fields.String(required=False, allow_none=False)


class PmsPropertyInfo(Datamodel):
    _name = "pms.property.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    company = fields.String(required=False, allow_none=True)
    defaultPricelistId = fields.Integer(required=False, allow_none=True)
    defaultAvailabilityPlanId = fields.Integer(required=False, allow_none=True)
    colorOptionConfig = fields.String(required=False, allow_none=True)
    preReservationColor = fields.String(required=False, allow_none=True)
    confirmedReservationColor = fields.String(required=False, allow_none=True)
    paidReservationColor = fields.String(required=False, allow_none=True)
    onBoardReservationColor = fields.String(required=False, allow_none=True)
    paidCheckinReservationColor = fields.String(required=False, allow_none=True)
    outReservationColor = fields.String(required=False, allow_none=True)
    staffReservationColor = fields.String(required=False, allow_none=True)
    toAssignReservationColor = fields.String(required=False, allow_none=True)
    pendingPaymentReservationColor = fields.String(required=False, allow_none=True)
    simpleOutColor = fields.String(required=False, allow_none=True)
    simpleInColor = fields.String(required=False, allow_none=True)
    simpleFutureColor = fields.String(required=False, allow_none=True)
