from marshmallow import Schema, fields

from odoo.addons.datamodel.core import Datamodel


class PmsReservationSchema(Schema):
    id = fields.Integer(required=True, allow_none=False)


class PmsFolioShortInfo(Datamodel):
    _name = "pms.folio.short.info"
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
