from marshmallow import fields, Schema
from typing import List
from odoo.addons.datamodel.core import Datamodel
from .pms_reservation_short_info import PmsReservationShortInfo


class PmsReservationSchema(Schema):

    id = fields.Integer(required=True, allow_none=False)
    checkin = fields.String(required=True, allow_none=True)
    checkout = fields.String(required=True, allow_none=True)
    preferredRoomId = fields.String(required=False, allow_none=True)
    roomTypeId = fields.String(required=False, allow_none=True)
    priceTotal = fields.Float(required=False, allow_none=True)
    adults = fields.Integer(required=False, allow_none=True)
    pricelist = fields.String(required=False, allow_none=True)



class PmsFolioShortInfo(Datamodel):
    _name = "pms.folio.short.info"

    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    partnerName = fields.String(required=False, allow_none=True)
    partnerPhone = fields.String(required=False, allow_none=True)
    partnerEmail = fields.String(required=False, allow_none=True)
    channelType = fields.String(required=False, allow_none=True)
    agency = fields.String(required=False, allow_none=True)
    # paymentState = fields.String(required=False, allow_none=True)
    state = fields.String(required=False, allow_none=True)
    pendingAmount = fields.Float(required=False, allow_none=True)
    reservations = fields.List(fields.Nested(PmsReservationSchema))

