from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class CivitfunApiRestUserInput(Datamodel):
    _name = "civitfun.api.rest.user.input"
    propertyId = fields.String(required=True, allow_none=False)


class CivitfunApiRestUserOutput(Datamodel):
    _name = "civitfun.api.rest.user.output"
    status = fields.String(required=True, allow_none=False)
    message = fields.String(required=True, allow_none=False)
    token = fields.String(required=False, allow_none=True)
