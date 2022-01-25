from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsPartnerInfo(Datamodel):
    _name = "pms.partner.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
