from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class PmsCalendarChanges(Datamodel):
    _name = "pms.calendar.changes"
    reservationLinesChanges = fields.List(fields.Dict(required=False, allow_none=True))
