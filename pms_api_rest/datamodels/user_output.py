from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsApiRestUserOutput(Datamodel):
    _name = "pms.api.rest.user.output"
    # user = fields.String(required=False, allow_none=True)
    # exp = fields.String(required=False, allow_none=True)
    token = fields.String(required=False, allow_none=True)
