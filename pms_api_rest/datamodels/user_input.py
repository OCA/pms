from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsApiRestUserInput(Datamodel):
    _name = "pms.api.rest.user.input"
    username = fields.String(required=False, allow_none=True)
    password = fields.String(required=False, allow_none=True)
