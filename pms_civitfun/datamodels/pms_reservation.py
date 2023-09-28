from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class CivitfunReservationSearchInfo(Datamodel):
    _name = "civitfun.reservation.search.info"

    propertyId = fields.String(required=False, allow_none=True)
    bookingIdentifier = fields.String(required=False, allow_none=True)
    bookingCode = fields.String(required=False, allow_none=True)
    entranceDate = fields.String(required=False, allow_none=True)
    departureDate = fields.String(required=False, allow_none=True)
    bookingDate = fields.String(required=False, allow_none=True)


class CivitfunReservationInfo(Datamodel):
    _name = "civitfun.reservation.info"

    bookingIdentifier = fields.String(required=False, allow_none=True)
    bookingCode = fields.String(required=False, allow_none=True)
    status = fields.String(required=False, allow_none=True)
    holder = fields.String(required=False, allow_none=True)
    holderCountry = fields.String(required=False, allow_none=True)
    email = fields.String(required=False, allow_none=True)
    entrance = fields.String(required=False, allow_none=True)
    entranceTime = fields.String(required=False, allow_none=True)
    departure = fields.String(required=False, allow_none=True)
    departureTime = fields.String(required=False, allow_none=True)
    adults = fields.Integer(required=False, allow_none=True)
    babies = fields.Integer(required=False, allow_none=True)
    children = fields.Integer(required=False, allow_none=True)
    regimeStay = fields.String(required=False, allow_none=True)
    agency = fields.String(required=False, allow_none=True)
    stayAmount = fields.Float(required=False, allow_none=True)
    depositAmount = fields.Float(required=False, allow_none=True)
    customerNotes = fields.String(required=False, allow_none=True)
    roomTypes = fields.List(fields.Dict(required=False, allow_none=True))
    reallocationPropertyId = fields.String(required=False, allow_none=True)
    additionalInfo = fields.List(fields.Dict(required=False, allow_none=True))
    guestsFilled = fields.Boolean(required=False, allow_none=True)
    guests = fields.List(NestedModel("civitfun.checkin.partner.info"))


class CivitfunBookingResults(Datamodel):
    _name = "civitfun.booking.results"

    success = fields.Boolean(required=False, allow_none=True)
    message = fields.String(required=False, allow_none=True)
    bookings = fields.List(NestedModel("civitfun.reservation.info"))
