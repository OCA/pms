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
    _check_company_auto = True

    reservation_id = fields.Many2one(
        string="Reservation",
        help="It is the reservation in a reservation line",
        required=True,
        copy=False,
        comodel_name="pms.reservation",
        ondelete="cascade",
        check_pms_properties=True,
    )
    room_id = fields.Many2one(
        string="Room",
        help="The room of a reservation. ",
        readonly=False,
        store=True,
        compute="_compute_room_id",
        comodel_name="pms.room",
        ondelete="restrict",
        check_pms_properties=True,
    )

    sale_line_ids = fields.Many2many(
        string="Sales Lines",
        readonly=True,
        copy=False,
        comodel_name="folio.sale.line",
        relation="reservation_line_sale_line_rel",
        column1="reservation_line_id",
        column2="sale_line_id",
        check_pms_properties=True,
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Property with access to the element;"
        " if not set, all properties can access",
        readonly=True,
        store=True,
        comodel_name="pms.property",
        related="reservation_id.pms_property_id",
        check_pms_properties=True,
    )
    date = fields.Date(
        string="Date",
        help="The date of the reservation in reservation line",
    )
    state = fields.Selection(
        string="State",
        help="State of the reservation line.",
        related="reservation_id.state",
        store=True,
    )
    price = fields.Float(
        string="Price",
        help="The price in a reservation line",
        store=True,
        readonly=False,
        digits=("Product Price"),
        compute="_compute_price",
    )
    cancel_discount = fields.Float(
        string="Cancelation Discount (%)",
        help="",
        readonly=False,
        default=0.0,
        store=True,
        digits=("Discount"),
        compute="_compute_cancel_discount",
    )
    avail_id = fields.Many2one(
        string="Availability Day",
        help="",
        store=True,
        comodel_name="pms.availability",
        ondelete="restrict",
        compute="_compute_avail_id",
        check_pms_properties=True,
    )

    discount = fields.Float(
        string="Discount (%)",
        help="",
        default=0.0,
        digits=("Discount"),
    )
    occupies_availability = fields.Boolean(
        string="Occupies",
        help="This record is taken into account to calculate availability",
        store=True,
        compute="_compute_occupies_availability",
    )
    impacts_quota = fields.Integer(
        string="Impacts quota",
        help="This line has been taken into account in the avail quota",
        readonly=False,
        store=True,
        compute="_compute_impact_quota",
    )

    _sql_constraints = [
        (
            "rule_availability",
            "EXCLUDE (room_id WITH =, date WITH =) \
            WHERE (occupies_availability = True)",
            "Room Occupied",
        ),
    ]

    def name_get(self):
        result = []
        for res in self:
            date = fields.Date.from_string(res.date)
            name = u"{}/{}".format(date.day, date.month)
            result.append((res.id, name))
        return result

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

    @api.depends("reservation_id.room_type_id", "reservation_id.preferred_room_id")
    def _compute_room_id(self):
        for line in self.filtered("reservation_id.room_type_id").sorted(
            key=lambda r: (r.reservation_id, r.date)
        ):
            reservation = line.reservation_id
            if (
                reservation.preferred_room_id
                and reservation.preferred_room_id != line.room_id
            ) or (
                (reservation.preferred_room_id or reservation.room_type_id)
                and not line.room_id
            ):
                free_room_select = True if reservation.preferred_room_id else False

                # we get the rooms available for the entire stay
                pms_property = line.pms_property_id
                pms_property = pms_property.with_context(
                    checkin=reservation.checkin,
                    checkout=reservation.checkout,
                    room_type_id=reservation.room_type_id.id
                    if not free_room_select
                    else False,
                    current_lines=reservation.reservation_line_ids.ids,
                    pricelist_id=reservation.pricelist_id.id,
                )
                rooms_available = pms_property.free_room_ids

                # Check if the room assigment is manual or automatic to set the
                # to_assign value on reservation
                manual_assigned = False
                if (
                    free_room_select
                    and reservation.preferred_room_id.id
                    not in reservation.reservation_line_ids.room_id.ids
                ):
                    # This case is a preferred_room_id manually assigned
                    manual_assigned = True
                # if there is availability for the entire stay
                if rooms_available:

                    # if the reservation has a preferred room
                    if reservation.preferred_room_id:

                        # if the preferred room is available
                        if reservation.preferred_room_id in rooms_available:
                            line.room_id = reservation.preferred_room_id
                            reservation.to_assign = (
                                False if manual_assigned else reservation.to_assign
                            )

                        # if the preferred room is NOT available
                        else:
                            if self.env.context.get("force_overbooking"):
                                reservation.overbooking = True
                                line.room_id = reservation.preferred_room_id
                            else:
                                raise ValidationError(
                                    _("%s: No room available in %s <-> %s.")
                                    % (
                                        reservation.preferred_room_id.name,
                                        reservation.checkin,
                                        reservation.checkout,
                                    )
                                )

                    # otherwise we assign the first of those
                    # available for the entire stay
                    else:
                        line.room_id = rooms_available[0]
                # check that the reservation cannot be allocated even by dividing it
                elif not self.env["pms.property"].splitted_availability(
                    checkin=reservation.checkin,
                    checkout=reservation.checkout,
                    room_type_id=reservation.room_type_id.id,
                    current_lines=line._origin.reservation_id.reservation_line_ids.ids,
                    pricelist=reservation.pricelist_id,
                    pms_property_id=line.pms_property_id.id,
                ):
                    if self.env.context.get("force_overbooking"):
                        reservation.overbooking = True
                        line.room_id = reservation.room_type_id.room_ids[0]
                    else:
                        raise ValidationError(
                            _("%s: No room type available")
                            % (reservation.room_type_id.name)
                        )

                # the reservation can be allocated into several rooms
                else:
                    rooms_ranking = dict()

                    # we go through the rooms of the type
                    for room in self.env["pms.room"].search(
                        [
                            ("room_type_id", "=", reservation.room_type_id.id),
                            ("pms_property_id", "=", reservation.pms_property_id.id),
                        ]
                    ):
                        # we iterate the dates from the date of the line to the checkout
                        for date_iterator in [
                            line.date + datetime.timedelta(days=x)
                            for x in range(0, (reservation.checkout - line.date).days)
                        ]:
                            # if the room is already assigned for
                            # a date we go to the next room
                            ids = reservation.reservation_line_ids.ids
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

                    if len(rooms_ranking) > 0:
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
                                    ("reservation_id", "=", reservation.id),
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

    @api.depends("reservation_id.room_type_id", "reservation_id.pricelist_id")
    def _compute_impact_quota(self):
        for line in self:
            reservation = line.reservation_id
            line.impacts_quota = self.env["pms.availability.plan"].update_quota(
                pricelist_id=reservation.pricelist_id,
                room_type_id=reservation.room_type_id,
                date=line.date,
                line=line,
            )

    @api.depends(
        "reservation_id",
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
            elif not line.price or self._context.get("force_recompute"):
                room_type_id = reservation.room_type_id.id
                product = self.env["pms.room.type"].browse(room_type_id).product_id
                partner = self.env["res.partner"].browse(reservation.partner_id.id)
                product = product.with_context(
                    lang=partner.lang,
                    partner=partner.id,
                    quantity=1,
                    date=reservation.date_order,
                    consumption_date=line.date,
                    pricelist=reservation.pricelist_id.id,
                    uom=product.uom_id.id,
                    property=reservation.pms_property_id.id,
                )
                line.price = self.env["account.tax"]._fix_tax_included_price_company(
                    line._get_display_price(product),
                    product.taxes_id,
                    reservation.tax_ids,
                    reservation.company_id,
                )
                # TODO: Out of service 0 amount

    @api.depends("reservation_id.state", "reservation_id.overbooking")
    def _compute_occupies_availability(self):
        for line in self:
            if line.reservation_id.state == "cancel" or line.reservation_id.overbooking:
                line.occupies_availability = False
            else:
                line.occupies_availability = True

    # TODO: Refact method and allowed cancelled single days
    @api.depends("reservation_id.cancelled_reason")
    def _compute_cancel_discount(self):
        for line in self:
            line.cancel_discount = 0
            reservation = line.reservation_id
            pricelist = reservation.pricelist_id
            if reservation.state == "cancel":
                if (
                    reservation.cancelled_reason
                    and pricelist
                    and pricelist.cancelation_rule_id
                ):
                    checkin = fields.Date.from_string(reservation.checkin)
                    checkout = fields.Date.from_string(reservation.checkout)
                    days = abs((checkin - checkout).days)
                    rule = pricelist.cancelation_rule_id
                    discount = 0
                    if reservation.cancelled_reason == "late":
                        discount = 100 - rule.penalty_late
                        if rule.apply_on_late == "first":
                            days = 1
                        elif rule.apply_on_late == "days":
                            days = rule.days_late
                    elif reservation.cancelled_reason == "noshow":
                        discount = 100 - rule.penalty_noshow
                        if rule.apply_on_noshow == "first":
                            days = 1
                        elif rule.apply_on_noshow == "days":
                            days = rule.days_late - 1
                    elif reservation.cancelled_reason == "intime":
                        discount = 100

                    dates = []
                    for i in range(0, days):
                        dates.append(
                            fields.Date.from_string(
                                fields.Date.from_string(checkin)
                                + datetime.timedelta(days=i)
                            )
                        )
                    reservation.reservation_line_ids.filtered(
                        lambda r: r.date in dates
                    ).update({"cancel_discount": discount})
                    reservation.reservation_line_ids.filtered(
                        lambda r: r.date not in dates
                    ).update({"cancel_discount": 100})
                else:
                    reservation.reservation_line_ids.update({"cancel_discount": 0})
            else:
                reservation.reservation_line_ids.update({"cancel_discount": 0})

    @api.depends("room_id", "pms_property_id", "date", "occupies_availability")
    def _compute_avail_id(self):
        for record in self:
            if record.room_id.room_type_id and record.date and record.pms_property_id:
                avail = self.env["pms.availability"].search(
                    [
                        ("date", "=", record.date),
                        ("room_type_id", "=", record.room_id.room_type_id.id),
                        ("pms_property_id", "=", record.pms_property_id.id),
                    ]
                )
                if avail:
                    record.avail_id = avail.id
                else:
                    record.avail_id = self.env["pms.availability"].create(
                        {
                            "date": record.date,
                            "room_type_id": record.room_id.room_type_id.id,
                            "pms_property_id": record.pms_property_id.id,
                        }
                    )
            else:
                record.avail_id = False

    # Constraints and onchanges
    @api.constrains("date")
    def constrains_duplicated_date(self):
        for record in self:
            duplicated = record.reservation_id.reservation_line_ids.filtered(
                lambda r: r.date == record.date and r.id != record.id
            )
            if duplicated:
                raise ValidationError(_("Duplicated reservation line date"))

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
