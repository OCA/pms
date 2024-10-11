from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsAvailSearchParam(Datamodel):
    _name = "pms.avail.search.param"
    availabilityFrom = fields.String(required=True, allow_none=True)
    availabilityTo = fields.String(required=True, allow_none=True)
    pmsPropertyId = fields.Integer(required=True, allow_none=True)
    pricelistId = fields.Integer(required=False, allow_none=True)
    roomTypeId = fields.Integer(required=False, allow_none=True)
    realAvail = fields.Boolean(required=False, allow_none=True)
    currentLines = fields.List(fields.Integer(), required=False, allow_none=False)


class PmsAvailInfo(Datamodel):
    _name = "pms.avail.info"
    date = fields.String(required=True, allow_none=False)
    roomIds = fields.List(fields.Integer, required=False, allow_none=True)


class BookiaAvailSearchParam(Datamodel):
    _name = "bookia.avail.search.param"
    checkin = fields.String(required=True, allow_none=True)
    checkout = fields.String(required=True, allow_none=True)
    pmsPropertyId = fields.Integer(required=True, allow_none=True)
    roomTypeId = fields.Integer(required=False, allow_none=True)
    occupancy = fields.Integer(required=False, allow_none=True)


class BookiaAvailInfo(Datamodel):
    _name = "bookia.avail.info"
    roomTypeId = fields.Integer(required=True, allow_none=False)
    roomTypeName = fields.String(required=True, allow_none=False)
    avail = fields.Integer(required=True, allow_none=False)
    price = fields.Float(required=True, allow_none=False)
