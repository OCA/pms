from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsApiRestUserInput(Datamodel):
    _name = "pms.api.rest.user.input"
    username = fields.String(required=False, allow_none=True)
    password = fields.String(required=False, allow_none=True)


class PmsApiRestUserOutput(Datamodel):
    _name = "pms.api.rest.user.output"
    token = fields.String(required=False, allow_none=True)
    userId = fields.Integer(required=True, allow_none=False)
    userName = fields.String(required=True, allow_none=False)
    userImageBase64 = fields.String(required=False, allow_none=True)
    defaultPropertyId = fields.Integer(required=True, allow_none=False)
    defaultPropertyName = fields.String(required=True, allow_none=False)
