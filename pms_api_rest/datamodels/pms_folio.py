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
    saleChannel = fields.String(required=False, allow_none=True)
    agency = fields.String(required=False, allow_none=True)
    state = fields.String(required=False, allow_none=True)
    pendingAmount = fields.Float(required=False, allow_none=True)
    reservations = fields.List(fields.Dict(required=False, allow_none=True))
    salesPerson = fields.String(required=False, allow_none=True)
    paymentState = fields.String(required=False, allow_none=True)
    propertyId = fields.Integer(required=False, allow_none=True)
    agencyImage = fields.String(required=False, allow_none=True)
