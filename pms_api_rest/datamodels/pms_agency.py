from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsAgencySearchParam(Datamodel):
    _name = "pms.agency.search.param"
    name = fields.String(required=False, allow_none=True)
    otas = fields.Boolean(required=False, allow_none=True)


class PmsAgencyInfo(Datamodel):
    _name = "pms.agency.info"
    id = fields.Integer(required=True, allow_none=False)
    name = fields.String(required=True, allow_none=False)
    imageUrl = fields.String(required=False, allow_none=True)
