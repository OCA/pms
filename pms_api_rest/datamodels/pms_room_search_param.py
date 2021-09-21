from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsRoomSearchParam(Datamodel):
    _name = "pms.room.search.param"

    id = fields.Integer(required=False, allow_none=False)
    name = fields.String(required=False, allow_none=False)
