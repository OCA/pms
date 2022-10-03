from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsResLangInfo(Datamodel):
    _name = "res.lang.info"
    code = fields.String(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
