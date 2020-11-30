# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime

from odoo import api, fields, models


class PmsRoomTypeRestriction(models.Model):
    """The room type restriction is used as a daily restriction plan for room types
    and therefore is related only with one property."""

    _name = "pms.room.type.restriction"
    _description = "Reservation restriction plan"

    # Default methods
    @api.model
    def _get_default_pms_property(self):
        return self.env.user.pms_property_id or None

    # Fields declaration
    name = fields.Char("Restriction Plan Name", required=True)
    pms_property_id = fields.Many2one(
        comodel_name="pms.property",
        string="Property",
        ondelete="restrict",
    )

    pms_pricelist_ids = fields.One2many(
        comodel_name="product.pricelist",
        inverse_name="restriction_id",
        string="Pricelists",
        required=False,
        ondelete="restrict",
    )

    item_ids = fields.One2many(
        comodel_name="pms.room.type.restriction.item",
        inverse_name="restriction_id",
        string="Restriction Items",
        copy=True,
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="If unchecked, it will allow you to hide the "
        "restriction plan without removing it.",
    )

    # Business Methods
    @classmethod
    def any_restriction_applies(cls, checkin, checkout, item):
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
        domain_restrictions = [
            ("date", ">=", checkin),
            ("date", "<=", checkout),
        ]

        if room_type_id:
            domain_rooms.append(("room_type_id", "=", room_type_id))
            domain_restrictions.append(("room_type_id", "=", room_type_id))

        free_rooms = self.env["pms.room"].search(domain_rooms)

        if pricelist:
            domain_restrictions.append(
                ("restriction_id.pms_pricelist_ids", "=", pricelist)
            )
            restriction_items = self.env["pms.room.type.restriction.item"].search(
                domain_restrictions
            )

            if len(restriction_items) > 0:
                room_types_to_remove = []
                for item in restriction_items:
                    if self.any_restriction_applies(checkin, checkout, item):
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
            restriction = self.env["pms.room.type.restriction.item"].search(
                [
                    ("restriction_id.pms_pricelist_ids", "=", pricelist_id.id),
                    ("room_type_id", "=", room_type_id.id),
                    ("date", "=", date),
                ]
            )
            # applies a restriction
            if restriction:
                restriction.ensure_one()
                if restriction and restriction.quota != -1 and restriction.quota > 0:

                    # the line has no restriction item applied before
                    if not line.impacts_quota:
                        restriction.quota -= 1
                        return restriction.id

                    # the line has a restriction item applied before
                    elif line.impacts_quota != restriction.id:

                        # decrement quota on current restriction_item
                        restriction.quota -= 1

                        # check old restricition item
                        old_restriction = self.env[
                            "pms.room.type.restriction.item"
                        ].search([("id", "=", line.impacts_quota)])

                        # restore quota in old restriction item
                        if old_restriction:
                            old_restriction.quota += 1

                        return restriction.id

        # in any case, check old restricition item
        if line.impacts_quota:
            old_restriction = self.env["pms.room.type.restriction.item"].search(
                [("id", "=", line.impacts_quota)]
            )
            # and restore quota in old restriction item
            if old_restriction:
                old_restriction.quota += 1

        return False
