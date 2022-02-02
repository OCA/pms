from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsSearchParam(Datamodel):
    _name = "pms.search.param"

    pms_property_id = fields.Integer(required=False, allow_none=True)
    pms_property_ids = fields.List(fields.Integer(), required=False)
