from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsNotificationSearch(Datamodel):
    _name = "pms.notification.search"
    pmsPropertyId = fields.Integer(required=False)
    fromDateTime = fields.String(required=False)


class PmsNotificationInfo(Datamodel):
    _name = "pms.notification.info"
    folioId = fields.Integer(required=False)
    dateTime = fields.String(required=False)
    userId = fields.Integer(required=False)
    mensaje = fields.String(required=False)
    pmsPropertyId = fields.Integer(required=False)
