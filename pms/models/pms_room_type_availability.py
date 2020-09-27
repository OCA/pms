# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# Copyright 2018  Pablo Quesada
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import timedelta

from odoo import api, fields, models


class PmsRoomTypeAvailability(models.Model):
    _name = "pms.room.type.availability"
    _description = "Availability"
    _inherit = "mail.thread"

    @api.model
    def _default_max_avail(self):
        return self.room_type_id.default_max_avail

    @api.model
    def _default_quota(self):
        return self.room_type_id.default_quota

    # Fields declaration
    room_type_id = fields.Many2one(
        "pms.room.type", "Room Type", required=True, ondelete="cascade"
    )
    date = fields.Date(
        "Date",
        required=True,
        tracking=True,
    )
    quota = fields.Integer(
        "Quota",
        default=_default_quota,
        tracking=True,
        help="Generic Quota assigned.",
    )
    max_avail = fields.Integer(
        "Max. Availability",
        default=-1,
        readonly=True,
        tracking=True,
        help="Maximum simultaneous availability on own Booking Engine.",
    )
    no_web = fields.Boolean(
        "No Web",
        default=False,
        tracking=True,
        help="Set zero availability to the own Booking Engine "
        "even when the availability is positive,",
    )

    _sql_constraints = [
        (
            "unique_availability_room_type_rule_date",
            "unique(room_type_id, date)",
            "The availability rule for this date in this room type already exists, "
            "modify it instead of trying to create a new one",
        ),
    ]

    # Business Methods
    @api.model
    def rooms_available(
        self, checkin, checkout, room_type_id=False, current_lines=False
    ):
        domain = self._get_domain_reservations_occupation(
            dfrom=checkin,
            dto=checkout - timedelta(1),
            current_lines=current_lines,
        )
        reservation_lines = self.env["pms.reservation.line"].search(domain)
        reservations_rooms = reservation_lines.mapped("room_id.id")
        free_rooms = self.env["pms.room"].search([("id", "not in", reservations_rooms)])
        if room_type_id:
            rooms_linked = (
                self.env["pms.room.type"].search([("id", "=", room_type_id)]).room_ids
            )
            free_rooms = free_rooms & rooms_linked
        return free_rooms.sorted(key=lambda r: r.sequence)

    @api.model
    def _get_domain_reservations_occupation(self, dfrom, dto, current_lines=False):
        if current_lines and not isinstance(current_lines, list):
            current_lines = [current_lines]
        domain = [
            ("date", ">=", dfrom),
            ("date", "<=", dto),
            ("occupies_availability", "=", True),
            ("id", "not in", current_lines),
        ]
        return domain
