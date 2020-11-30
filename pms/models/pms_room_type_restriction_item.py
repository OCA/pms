# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PmsRoomTypeRestrictionItem(models.Model):
    _name = "pms.room.type.restriction.item"
    _description = "Reservation restriction by day"

    # Field Declarations

    restriction_id = fields.Many2one(
        comodel_name="pms.room.type.restriction",
        string="Restriction Plan",
        ondelete="cascade",
        index=True,
    )
    room_type_id = fields.Many2one(
        comodel_name="pms.room.type",
        string="Room Type",
        required=True,
        ondelete="cascade",
    )
    date = fields.Date(string="Date")

    min_stay = fields.Integer(
        string="Min. Stay",
        default=0,
    )
    min_stay_arrival = fields.Integer(
        string="Min. Stay Arrival",
        default=0,
    )
    max_stay = fields.Integer(
        string="Max. Stay",
        default=0,
    )
    max_stay_arrival = fields.Integer(
        string="Max. Stay Arrival",
        default=0,
    )
    closed = fields.Boolean(
        string="Closed",
        default=False,
    )
    closed_departure = fields.Boolean(
        string="Closed Departure",
        default=False,
    )
    closed_arrival = fields.Boolean(
        string="Closed Arrival",
        default=False,
    )
    quota = fields.Integer(
        string="Quota",
        store=True,
        readonly=False,
        compute="_compute_quota",
        help="Generic Quota assigned.",
    )

    max_avail = fields.Integer(
        string="Max. Availability",
        store=True,
        readonly=False,
        compute="_compute_max_avail",
        help="Maximum simultaneous availability on own Booking Engine.",
    )

    _sql_constraints = [
        (
            "room_type_registry_unique",
            "unique(restriction_id, room_type_id, date)",
            "Only can exists one restriction in the same \
                         day for the same room type!",
        )
    ]

    @api.depends("room_type_id")
    def _compute_quota(self):
        for record in self:
            if not record.quota:
                record.quota = record.room_type_id.default_quota

    @api.depends("room_type_id")
    def _compute_max_avail(self):
        for record in self:
            if not record.max_avail:
                record.max_avail = record.room_type_id.default_max_avail

    @api.constrains("min_stay", "min_stay_arrival", "max_stay", "max_stay_arrival")
    def _check_min_max_stay(self):
        for record in self:
            if record.min_stay < 0:
                raise ValidationError(_("Min. Stay can't be less than zero"))
            elif record.min_stay_arrival < 0:
                raise ValidationError(_("Min. Stay Arrival can't be less than zero"))
            elif record.max_stay < 0:
                raise ValidationError(_("Max. Stay can't be less than zero"))
            elif record.max_stay_arrival < 0:
                raise ValidationError(_("Max. Stay Arrival can't be less than zero"))
            elif (
                record.min_stay != 0
                and record.max_stay != 0
                and record.min_stay > record.max_stay
            ):
                raise ValidationError(_("Max. Stay can't be less than Min. Stay"))
            elif (
                record.min_stay_arrival != 0
                and record.max_stay_arrival != 0
                and record.min_stay_arrival > record.max_stay_arrival
            ):
                raise ValidationError(
                    _("Max. Stay Arrival can't be less than Min. Stay Arrival")
                )
