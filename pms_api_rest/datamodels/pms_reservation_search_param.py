from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsReservationSearchParam(Datamodel):
    _name = "pms.reservation.search.param"

    id = fields.Integer(required=False, allow_none=False)
    name = fields.String(required=False, allow_none=False)
