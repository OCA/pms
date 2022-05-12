from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsUbicationSearchParam(Datamodel):
    _name = "pms.ubication.search.param"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    pms_property_ids = fields.List(fields.Integer(), required=False)


class PmsUbicationInfo(Datamodel):
    _name = "pms.ubication.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    pms_property_ids = fields.List(fields.Integer(), required=False)
