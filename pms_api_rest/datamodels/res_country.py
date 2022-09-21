from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsResCountriesInfo(Datamodel):
    _name = "res.country.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
    code = fields.String(required=False, allow_none=True)


class PmsResCountryStatesInfo(Datamodel):
    _name = "res.country_state.info"
    id = fields.Integer(required=False, allow_none=True)
    name = fields.String(required=False, allow_none=True)
