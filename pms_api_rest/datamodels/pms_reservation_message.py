from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class PmsReservationMessageInfo(Datamodel):
    _name = "pms.reservation.message.info"
    reservationId = fields.Integer(required=False, allow_none=True)
    author = fields.String(required=False, allow_none=True)
    message = fields.String(required=False, allow_none=True)
    subject = fields.String(required=False, allow_none=True)
    date = fields.String(required=False, allow_none=True)
    messageType = fields.String(required=False, allow_none=True)
    authorImageBase64 = fields.String(required=False, allow_none=True)


class PmsFolioMessageInfo(Datamodel):
    _name = "pms.folio.message.info"
    author = fields.String(required=False, allow_none=True)
    message = fields.String(required=False, allow_none=True)
    subject = fields.String(required=False, allow_none=True)
    date = fields.String(required=False, allow_none=True)
    messageType = fields.String(required=False, allow_none=True)
    authorImageBase64 = fields.String(required=False, allow_none=True)


class PmsMessageInfo(Datamodel):
    _name = "pms.message.info"
    folioMessages = fields.List(
        NestedModel("pms.reservation.message.info"), required=False, allow_none=True
    )
    reservationMessages = fields.List(
        NestedModel("pms.reservation.message.info"), required=False, allow_none=True
    )
