# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PmsReservationLine(models.Model):
    _name = "pms.reservation.line"
    _description = "Reservations by day"
    _order = "date"

    # Default Methods ang Gets

    def name_get(self):
        result = []
        for res in self:
            date = fields.Date.from_string(res.date)
            name = u"{}/{}".format(date.day, date.month)
            result.append((res.id, name))
        return result

    # Fields declaration
    reservation_id = fields.Many2one(
        "pms.reservation",
        string="Reservation",
        ondelete="cascade",
        required=True,
        copy=False,
    )
    room_id = fields.Many2one(
        "pms.room",
        string="Room",
        ondelete="restrict",
        compute="_compute_room_id",
        store=True,
        readonly=False,
    )
    move_line_ids = fields.Many2many(
        "account.move.line",
        "reservation_line_move_rel",
        "reservation_line_id",
        "move_line_id",
        string="Invoice Lines",
        readonly=True,
        copy=False,
    )
    pms_property_id = fields.Many2one(
        "pms.property",
        store=True,
        readonly=True,
        related="reservation_id.pms_property_id",
    )
    date = fields.Date("Date")
    state = fields.Selection(related="reservation_id.state")
    price = fields.Float(
        string="Price",
        digits=("Product Price"),
        compute="_compute_price",
        store=True,
        readonly=False,
    )
    cancel_discount = fields.Float(
        string="Cancel Discount (%)",
        digits=("Discount"),
        default=0.0,
        compute="_compute_cancel_discount",
        store=True,
        readonly=False,
    )
    discount = fields.Float(string="Discount (%)", digits=("Discount"), default=0.0)
    occupies_availability = fields.Boolean(
        string="Occupies",
        compute="_compute_occupies_availability",
        store=True,
        help="This record is taken into account to calculate availability",
    )

    _sql_constraints = [
        (
            "rule_availability",
            "EXCLUDE (room_id WITH =, date WITH =) \
            WHERE (occupies_availability = True)",
            "Room Occupied",
        ),
    ]

    # Compute and Search methods
    @api.depends("reservation_id.room_type_id")
    def _compute_room_id(self):
        for line in self.sorted(key=lambda r: (r.reservation_id, r.date)):

            # if the reservation has a room type and no room id
            if line.reservation_id.room_type_id and not line.room_id:

                # we get the rooms available for the entire stay
                rooms_available = self.env[
                    "pms.room.type.availability"
                ].rooms_available(
                    checkin=line.reservation_id.checkin,
                    checkout=line.reservation_id.checkout,
                    room_type_id=line.reservation_id.room_type_id.id,
                    current_lines=line._origin.reservation_id.reservation_line_ids.ids,
                )

                # if there is availability for the entire stay
                if rooms_available:

                    # if the reservation has a preferred room
                    if line.reservation_id.preferred_room_id:

                        # if the preferred room is available
                        if line.reservation_id.preferred_room_id in rooms_available:
                            line.room_id = line.reservation_id.preferred_room_id

                        # if the preferred room is NOT available
                        else:
                            raise ValidationError(
                                _("%s: No room available.")
                                % (line.reservation_id.preferred_room_id.name)
                            )

                    # otherwise we assign the first of those
                    # available for the entire stay
                    else:
                        line.room_id = rooms_available[0]

                # if there is no availability for the entire stay without
                # changing rooms (we assume a split reservation)
                else:
                    rooms_ranking = dict()

                    # we go through the rooms of the type
                    for room in self.env["pms.room"].search(
                        [("room_type_id", "=", line.reservation_id.room_type_id.id)]
                    ):

                        # we iterate the dates from the date of the line to the checkout
                        for date_iterator in [
                            line.date + datetime.timedelta(days=x)
                            for x in range(
                                0, (line.reservation_id.checkout - line.date).days
                            )
                        ]:
                            # if the room is already assigned for
                            # a date we go to the next room
                            ids = line.reservation_id.reservation_line_ids.ids
                            if (
                                self.env["pms.reservation.line"].search_count(
                                    [
                                        ("date", "=", date_iterator),
                                        ("room_id", "=", room.id),
                                        ("id", "not in", ids),
                                        ("occupies_availability", "=", True),
                                    ]
                                )
                                > 0
                            ):
                                break
                            # if the room is not assigned for a date we
                            # add it to the ranking / update its ranking
                            else:
                                rooms_ranking[room.id] = (
                                    1
                                    if room.id not in rooms_ranking
                                    else rooms_ranking[room.id] + 1
                                )
                    if len(rooms_ranking) == 0:
                        raise ValidationError(
                            _("%s: No room type available")
                            % (line.reservation_id.room_type_id.name)
                        )
                    else:
                        # we get the best score in the ranking
                        best = max(rooms_ranking.values())

                        # we keep the rooms with the best ranking
                        bests = {
                            key: value
                            for (key, value) in rooms_ranking.items()
                            if value == best
                        }

                        # if there is a tie in the rankings
                        if len(bests) > 1:

                            # we get the line from last night
                            date_last_night = line.date + datetime.timedelta(days=-1)
                            line_past_night = self.env["pms.reservation.line"].search(
                                [
                                    ("date", "=", date_last_night),
                                    ("reservation_id", "=", line.reservation_id.id),
                                ]
                            )
                            # if there is the night before and if the room
                            # from the night before is in the ranking
                            if line_past_night and line_past_night.room_id.id in bests:
                                line.room_id = line_past_night.room_id.id

                            # if the room from the night before is not in the ranking
                            # or there is no night before
                            else:
                                # At this point we set the room with the best ranking,
                                # no matter what it is
                                line.room_id = list(bests.keys())[0]

                        # if there is no tie in the rankings
                        else:
                            # At this point we set the room with the best ranking,
                            # no matter what it is
                            line.room_id = list(bests.keys())[0]

    @api.depends(
        "reservation_id",
        "reservation_id.pricelist_id",
        "reservation_id.room_type_id",
        "reservation_id.reservation_type",
        "reservation_id.pms_property_id",
    )
    def _compute_price(self):
        for line in self:
            reservation = line.reservation_id
            if (
                not reservation.room_type_id
                or not reservation.pricelist_id
                or not reservation.pms_property_id
            ):
                line.price = 0
            elif line._recompute_price():
                room_type_id = reservation.room_type_id.id
                product = self.env["pms.room.type"].browse(room_type_id).product_id
                partner = self.env["res.partner"].browse(reservation.partner_id.id)
                product = product.with_context(
                    lang=partner.lang,
                    partner=partner.id,
                    quantity=1,
                    date=line.date,
                    pricelist=reservation.pricelist_id.id,
                    uom=product.uom_id.id,
                    property=reservation.pms_property_id.id,
                )
                line.price = self.env["account.tax"]._fix_tax_included_price_company(
                    line._get_display_price(product),
                    product.taxes_id,
                    line.reservation_id.tax_ids,
                    line.reservation_id.company_id,
                )
                # TODO: Out of service 0 amount
            else:
                line.price = line._origin.price

    @api.depends("reservation_id.state", "reservation_id.overbooking")
    def _compute_occupies_availability(self):
        for line in self:
            if (
                line.reservation_id.state == "cancelled"
                or line.reservation_id.overbooking
            ):
                line.occupies_availability = False
            else:
                line.occupies_availability = True

    def _recompute_price(self):
        # REVIEW: Conditional to avoid overriding already calculated prices,
        # I'm not sure it's the best way
        self.ensure_one()
        origin = self._origin.reservation_id
        new = self.reservation_id
        price_fields = [
            "pricelist_id",
            "room_type_id",
            "reservation_type",
            "pms_property_id",
        ]
        if (
            any(origin[field] != new[field] for field in price_fields)
            or self._origin.price == 0
        ):
            return True
        return False

    # TODO: Refact method and allowed cancelled single days
    @api.depends("reservation_id.cancelled_reason")
    def _compute_cancel_discount(self):
        for line in self:
            line.cancel_discount = 0
            # reservation = line.reservation_id
            # pricelist = reservation.pricelist_id
            # if reservation.state == "cancelled":
            #     # TODO: Set 0 qty on cancel room services change to compute day_qty
            #     # (view constrain service_line_days)
            #     for service in reservation.service_ids:
            #         service.service_line_ids.write({"day_qty": 0})
            #         service._compute_days_qty()
            #     if (
            #         reservation.cancelled_reason
            #         and pricelist
            #         and pricelist.cancelation_rule_id
            #     ):
            #         date_start_dt = fields.Date.from_string(
            #             reservation.checkin
            #         )
            #         date_end_dt = fields.Date.from_string(
            #             reservation.checkout
            #         )
            #         days = abs((date_end_dt - date_start_dt).days)
            #         rule = pricelist.cancelation_rule_id
            #         if reservation.cancelled_reason == "late":
            #             discount = 100 - rule.penalty_late
            #             if rule.apply_on_late == "first":
            #                 days = 1
            #             elif rule.apply_on_late == "days":
            #                 days = rule.days_late
            #         elif reservation.cancelled_reason == "noshow":
            #             discount = 100 - rule.penalty_noshow
            #             if rule.apply_on_noshow == "first":
            #                 days = 1
            #             elif rule.apply_on_noshow == "days":
            #                 days = rule.days_late - 1
            #         elif reservation.cancelled_reason == "intime":
            #             discount = 100

            #         checkin = reservation.checkin
            #         dates = []
            #         for i in range(0, days):
            #             dates.append(
            #                 (
            #                     fields.Date.from_string(checkin) + timedelta(days=i)
            #                 ).strftime(DEFAULT_SERVER_DATE_FORMAT)
            #             )
            #         reservation.reservation_line_ids.filtered(
            #             lambda r: r.date in dates
            #         ).update({"cancel_discount": discount})
            #         reservation.reservation_line_ids.filtered(
            #             lambda r: r.date not in dates
            #         ).update({"cancel_discount": 100})
            #     else:
            #         reservation.reservation_line_ids.update({"cancel_discount": 0})
            # else:
            #     reservation.reservation_line_ids.update({"cancel_discount": 0})

    # Constraints and onchanges
    @api.constrains("date")
    def constrains_duplicated_date(self):
        for record in self:
            duplicated = record.reservation_id.reservation_line_ids.filtered(
                lambda r: r.date == record.date and r.id != record.id
            )
            if duplicated:
                raise ValidationError(_("Duplicated reservation line date"))

    @api.constrains("state")
    def constrains_service_cancel(self):
        for record in self:
            if record.state == "cancelled":
                room_services = record.reservation_id.service_ids
                for service in room_services:
                    cancel_lines = service.service_line_ids.filtered(
                        lambda r: r.date == record.date
                    )
                    cancel_lines.day_qty = 0

    def _get_display_price(self, product):
        if self.reservation_id.pricelist_id.discount_policy == "with_discount":
            return product.with_context(
                pricelist=self.reservation_id.pricelist_id.id
            ).price
        product_context = dict(
            self.env.context,
            partner_id=self.reservation_id.partner_id.id,
            date=self.date,
            uom=product.uom_id.id,
        )
        final_price, rule_id = self.reservation_id.pricelist_id.with_context(
            product_context
        ).get_product_price_rule(product, 1.0, self.reservation_id.partner_id)
        base_price, currency = self.with_context(
            product_context
        )._get_real_price_currency(
            product, rule_id, 1, product.uom_id, self.reservation_id.pricelist_id.id
        )
        if currency != self.reservation_id.pricelist_id.currency_id:
            base_price = currency._convert(
                base_price,
                self.reservation_id.pricelist_id.currency_id,
                self.reservation_id.company_id or self.env.company,
                fields.Date.today(),
            )
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    @api.constrains("room_id")
    def _check_adults(self):
        for record in self.filtered("room_id"):
            extra_bed = record.reservation_id.service_ids.filtered(
                lambda r: r.product_id.is_extra_bed is True
            )
            if (
                record.reservation_id.adults + record.reservation_id.children_occupying
                > record.room_id.get_capacity(len(extra_bed))
            ):
                raise ValidationError(_("Persons can't be higher than room capacity"))
            # if record.reservation_id.adults == 0:
            #    raise ValidationError(_("Reservation has no adults"))
