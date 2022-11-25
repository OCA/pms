from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsNotificationSearch(Datamodel):
    _name = "pms.notification.search"
    fromTimestamp = fields.String(required=False)


class PmsNotificationInfo(Datamodel):
    _name = "pms.notification.info"
    pmsPropertyId = fields.Integer(required=False)
    folioId = fields.Integer(required=False)
    timeStamp = fields.Integer(required=False)
    folioName = fields.String(required=False)
    partnerName = fields.String(required=False)
    saleChannelName = fields.String(required=False, allow_none=True)
