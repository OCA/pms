from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class PmsFolioSearchParam(Datamodel):
    _name = "pms.folio.search.param"
    _inherit = "pms.rest.metadata"
    pmsPropertyId = fields.Integer(required=True, allow_none=True)
    dateFrom = fields.String(required=False, allow_none=True)
    dateTo = fields.String(required=False, allow_none=True)
    filter = fields.String(required=False, allow_none=True)
    filterByState = fields.String(required=False, allow_none=True)


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
    pendingAmount = fields.Float(required=False, allow_none=True)
    firstCheckin = fields.String(required=False, allow_none=True)
    lastCheckout = fields.String(required=False, allow_none=True)
    createDate = fields.String(required=False, allow_none=True)
    pmsPropertyId = fields.Integer(required=False, allow_none=True)
    partnerId = fields.Integer(required=False, allow_none=True)
    reservations = fields.List(
        NestedModel("pms.reservation.info"), required=False, allow_none=True
    )
    pricelistId = fields.Integer(required=False, allow_none=True)
    saleChannelId = fields.Integer(required=False, allow_none=True)
    agencyId = fields.Integer(required=False, allow_none=True)
    externalReference = fields.String(required=False, allow_none=True)
    closureReasonId = fields.Integer(required=False, allow_none=True)
    outOfServiceDescription = fields.String(required=False, allow_none=True)
    preconfirm = fields.Boolean(required=False, allow_none=True)
    internalComment = fields.String(required=False, allow_none=True)
    # REVIEW: Mail workflow folio
    sendConfirmationMail = fields.Boolean(required=False, allow_none=True)
    cancelReservations = fields.Boolean(required=False, allow_none=True)
    confirmReservations = fields.Boolean(required=False, allow_none=True)
    invoiceStatus = fields.String(required=False, allow_none=True)
    portalUrl = fields.String(required=False, allow_none=True)
    language = fields.String(required=False, allow_none=True)


class PmsFolioShortInfo(Datamodel):
    _name = "pms.folio.short.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    state = fields.String(required=False, allow_none=True)
    partnerName = fields.String(required=False, allow_none=True)
    partnerPhone = fields.String(required=False, allow_none=True)
    partnerEmail = fields.String(required=False, allow_none=True)
    amountTotal = fields.Float(required=False, allow_none=True)
    pendingAmount = fields.Float(required=False, allow_none=True)
    paymentStateCode = fields.String(required=False, allow_none=True)
    paymentStateDescription = fields.String(required=False, allow_none=True)
    reservations = fields.List(fields.Dict(required=False, allow_none=True))
    reservationType = fields.String(required=False, allow_none=True)
    closureReasonId = fields.Integer(required=False, allow_none=True)
    agencyId = fields.Integer(required=False, allow_none=True)
    pricelistId = fields.Integer(required=False, allow_none=True)
    saleChannelId = fields.Integer(required=False, allow_none=True)
    firstCheckin = fields.String(required=False, allow_none=True)
    lastCheckout = fields.String(required=False, allow_none=True)
