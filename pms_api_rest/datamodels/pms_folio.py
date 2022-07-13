from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsFolioSearchParam(Datamodel):
    _name = "pms.folio.search.param"

    pmsPropertyId = fields.Integer(required=True, allow_none=True)
    dateFrom = fields.String(required=False, allow_none=True)
    dateTo = fields.String(required=False, allow_none=True)
    filter = fields.String(required=False, allow_none=True)


class PmsFolioInfo(Datamodel):
    _name = "pms.folio.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    partnerName = fields.String(required=False, allow_none=True)
    partnerPhone = fields.String(required=False, allow_none=True)
    partnerEmail = fields.String(required=False, allow_none=True)
    state = fields.String(required=False, allow_none=True)
    amountTotal = fields.Float(required=False, allow_none=True)
    reservationType = fields.String(required=False, allow_none=True)


class PmsFolioShortInfo(Datamodel):
    _name = "pms.folio.short.info"
    id = fields.Integer(required=False, allow_none=True)
    partnerName = fields.String(required=False, allow_none=True)
    partnerPhone = fields.String(required=False, allow_none=True)
    partnerEmail = fields.String(required=False, allow_none=True)
    amountTotal = fields.Float(required=False, allow_none=True)
    paymentStateCode = fields.String(required=False, allow_none=True)
    paymentStateDescription = fields.String(required=False, allow_none=True)
    reservations = fields.List(fields.Dict(required=False, allow_none=True))
