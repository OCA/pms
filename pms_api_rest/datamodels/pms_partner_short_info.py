from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsPartnerShortInfo(Datamodel):
    _name = "pms.partner.short.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
