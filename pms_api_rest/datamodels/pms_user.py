from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsApiRestUserInput(Datamodel):
    _name = "pms.api.rest.user.input"
    username = fields.String(required=False, allow_none=True)
    password = fields.String(required=False, allow_none=True)
    newPassword = fields.String(required=False, allow_none=True)
    userId = fields.Integer(required=False, allow_none=True)
    userEmail = fields.String(required=False, allow_none=True)
    resetToken = fields.String(required=False, allow_none=True)
    url = fields.String(required=False, allow_none=True)


class PmsApiRestUserOutput(Datamodel):
    _name = "pms.api.rest.user.output"
    token = fields.String(required=False, allow_none=True)
    expirationDate = fields.Integer(required=False, allow_none=True)
    userId = fields.Integer(required=True, allow_none=False)
    userName = fields.String(required=True, allow_none=False)
    userFirstName = fields.String(required=False, allow_none=True)
    userEmail = fields.String(required=False, allow_none=True)
    userPhone = fields.String(required=False, allow_none=True)
    userImageBase64 = fields.String(required=False, allow_none=True)
    defaultPropertyId = fields.Integer(required=False, allow_none=True)
    defaultPropertyName = fields.String(required=False, allow_none=True)
    isNewInterfaceUser = fields.Boolean(required=False, allow_none=True)
    availabilityRuleFields = fields.List(
        fields.String(), required=False, allow_none=True
    )

class PmsApiRestUserLoginOutput(Datamodel):
    _name = "pms.api.rest.user.login.output"
    login = fields.String(required=True, allow_none=False)
