from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsSearchParam(Datamodel):
    _name = "pms.search.param"

    pms_property_id = fields.Integer(required=True, allow_none=False)
