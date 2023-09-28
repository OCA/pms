from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsResUsersInfo(Datamodel):
    _name = "res.users.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    userImageBase64 = fields.String(required=False, allow_none=True)
