from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsSearchParam(Datamodel):
    _name = "pms.search.param"

    pmsPropertyId = fields.Integer(required=False, allow_none=True)
    pmsPropertyIds = fields.List(fields.Integer(), required=False)
