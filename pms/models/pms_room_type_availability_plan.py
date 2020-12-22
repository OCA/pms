# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime

from odoo import api, fields, models


class PmsRoomTypeAvailability(models.Model):
    """The room type availability is used as a daily availability plan for room types
    and therefore is related only with one property."""

    _name = "pms.room.type.availability.plan"
    _description = "Reservation availability plan"

    # Default methods
    @api.model
    def _get_default_pms_property(self):
        return self.env.user.pms_property_id or None

    # Fields declaration
    name = fields.Char("Availability Plan Name", required=True)
    pms_property_id = fields.Many2one(
        comodel_name="pms.property",
        string="Property",
        ondelete="restrict",
    )

    pms_pricelist_ids = fields.One2many(
        comodel_name="product.pricelist",
        inverse_name="availability_plan_id",
        string="Pricelists",
        required=False,
    )

    rule_ids = fields.One2many(
        comodel_name="pms.room.type.availability.rule",
        inverse_name="availability_plan_id",
        string="Availability Rules",
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="If unchecked, it will allow you to hide the "
        "Availability plan without removing it.",
    )

    # Business Methods
    @classmethod
    def any_rule_applies(cls, checkin, checkout, item):
        reservation_len = (checkout - checkin).days
        return any(
            [
                (0 < item.max_stay < reservation_len),
                (0 < item.min_stay > reservation_len),
                (0 < item.max_stay_arrival < reservation_len and checkin == item.date),
                (0 < item.min_stay_arrival > reservation_len and checkin == item.date),
                item.closed,
                (item.closed_arrival and checkin == item.date),
                (item.closed_departure and checkout == item.date),
                (item.quota == 0 or item.max_avail == 0),
            ]
        )

    @api.model
    def rooms_available(
        self,
        checkin,
        checkout,
        room_type_id=False,
        current_lines=False,
        pricelist=False,
    ):
        if current_lines and not isinstance(current_lines, list):
            current_lines = [current_lines]

        rooms_not_avail = (
            self.env["pms.reservation.line"]
            .search(
                [
                    ("date", ">=", checkin),
                    ("date", "<=", checkout - datetime.timedelta(1)),
                    ("occupies_availability", "=", True),
                    ("id", "not in", current_lines if current_lines else []),
                ]
            )
            .mapped("room_id.id")
        )

        domain_rooms = [
            ("id", "not in", rooms_not_avail if len(rooms_not_avail) > 0 else [])
        ]
        domain_rules = [
            ("date", ">=", checkin),
            ("date", "<=", checkout),
        ]

        if room_type_id:
            domain_rooms.append(("room_type_id", "=", room_type_id))
            domain_rules.append(("room_type_id", "=", room_type_id))

        free_rooms = self.env["pms.room"].search(domain_rooms)

        if pricelist:
            domain_rules.append(
                ("availability_plan_id.pms_pricelist_ids", "=", pricelist)
            )
            rule_items = self.env["pms.room.type.availability.rule"].search(
                domain_rules
            )

            if len(rule_items) > 0:
                room_types_to_remove = []
                for item in rule_items:
                    if self.any_rule_applies(checkin, checkout, item):
                        room_types_to_remove.append(item.room_type_id.id)
                free_rooms = free_rooms.filtered(
                    lambda x: x.room_type_id.id not in room_types_to_remove
                )

        return free_rooms.sorted(key=lambda r: r.sequence)

    @api.model
    def splitted_availability(
        self,
        checkin,
        checkout,
        room_type_id=False,
        current_lines=False,
        pricelist=False,
    ):
        for date_iterator in [
            checkin + datetime.timedelta(days=x)
            for x in range(0, (checkout - checkin).days)
        ]:
            rooms_avail = self.rooms_available(
                checkin=date_iterator,
                checkout=date_iterator + datetime.timedelta(1),
                room_type_id=room_type_id,
                current_lines=current_lines,
                pricelist=pricelist.id,
            )
            if len(rooms_avail) < 1:
                return False
        return True

    @api.model
    def update_quota(self, pricelist_id, room_type_id, date, line):
        if pricelist_id and room_type_id and date:
            rule = self.env["pms.room.type.availability.rule"].search(
                [
                    ("availability_plan_id.pms_pricelist_ids", "=", pricelist_id.id),
                    ("room_type_id", "=", room_type_id.id),
                    ("date", "=", date),
                ]
            )
            # applies a rule
            if rule:
                rule.ensure_one()
                if rule and rule.quota != -1 and rule.quota > 0:

                    # the line has no rule item applied before
                    if not line.impacts_quota:
                        rule.quota -= 1
                        return rule.id

                    # the line has a rule item applied before
                    elif line.impacts_quota != rule.id:

                        # decrement quota on current rule item
                        rule.quota -= 1

                        # check old rule item
                        old_rule = self.env["pms.room.type.availability.rule"].search(
                            [("id", "=", line.impacts_quota)]
                        )

                        # restore quota in old rule item
                        if old_rule:
                            old_rule.quota += 1

                        return rule.id

        # in any case, check old rule item
        if line.impacts_quota:
            old_rule = self.env["pms.room.type.availability.rule"].search(
                [("id", "=", line.impacts_quota)]
            )
            # and restore quota in old rule item
            if old_rule:
                old_rule.quota += 1

        return False

    # Action methods
    def open_massive_changes_wizard(self):

        if self.ensure_one():
            return {
                "view_type": "form",
                "view_mode": "form",
                "name": "Massive changes on Availability Plan: " + self.name,
                "res_model": "pms.massive.changes.wizard",
                "target": "new",
                "type": "ir.actions.act_window",
                "context": {
                    "availability_plan_id": self.id,
                },
            }
