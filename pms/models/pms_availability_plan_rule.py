# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError


class PmsAvailabilityPlanRule(models.Model):
    """Sale restrictions of a rate, by date range.

    One record covers every night between ``date_from`` and ``date_to``, both
    included, so a season is one row instead of one per day.

    INVARIANT: overlapping records are legal and are resolved when READING,
    the one written last winning the nights they share. That is how a season
    is overridden for a shorter period without cutting it up, and it is why
    there is no unique key on (plan, room type, night).
    """

    _name = "pms.availability.plan.rule"
    _description = "Reservation rule by date range"
    _check_pms_properties_auto = True
    _order = (
        "availability_plan_id, pms_property_id, room_type_id, "
        "date_from, write_date desc, id desc"
    )

    availability_plan_id = fields.Many2one(
        string="Availability Plan",
        help="The availability plan that include the Availabilty Rule",
        index=True,
        comodel_name="pms.availability.plan",
        ondelete="cascade",
        check_pms_properties=True,
    )
    room_type_id = fields.Many2one(
        string="Room Type",
        help="Room type for which availability rule is applied",
        required=True,
        index=True,
        comodel_name="pms.room.type",
        ondelete="cascade",
        check_pms_properties=True,
    )
    date_from = fields.Date(
        string="From",
        help="First night the rule applies to, included",
        required=True,
    )
    date_to = fields.Date(
        string="To",
        help="Last night the rule applies to, included",
        required=True,
    )

    min_stay = fields.Integer(
        string="Min. Stay",
        help="Minimum stay",
        default=0,
    )
    min_stay_arrival = fields.Integer(
        string="Min. Stay Arrival",
        help="Minimum stay if checkin is today",
        default=0,
    )
    max_stay = fields.Integer(
        string="Max. Stay",
        help="Maximum stay",
        default=0,
    )
    max_stay_arrival = fields.Integer(
        string="Max. Stay Arrival",
        help="Maximum stay if checkin is today",
        default=0,
    )
    closed = fields.Boolean(
        help="Indicate if property is closed or not",
        default=False,
    )
    closed_departure = fields.Boolean(
        default=False,
    )
    closed_arrival = fields.Boolean(
        default=False,
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Properties with access to the element",
        ondelete="restrict",
        required=True,
        index=True,
        comodel_name="pms.property",
        check_pms_properties=True,
    )

    _sql_constraints = [
        (
            "date_range",
            "CHECK (date_to >= date_from)",
            "The last night of an availability rule cannot be before the first one!",
        ),
    ]

    def _auto_init(self):
        res = super()._auto_init()
        # The resolver always asks for one plan and one property over a window
        # of dates, and no single column index prunes that: ``date_from <=
        # end`` holds for every rule in the past, which is what accumulates.
        # Hence ``date_to`` first, the selective half.
        tools.create_index(
            self._cr,
            "pms_availability_plan_rule_plan_property_date_index",
            self._table,
            ["availability_plan_id", "pms_property_id", "date_to", "date_from"],
        )
        return res

    @api.model
    def _resolve_rules(
        self,
        availability_plan_id,
        pms_property_id,
        date_from,
        date_to,
        room_type_ids=None,
    ):
        """Expand the ranges of a plan into the rule that wins on every night.

        :param date_from: first night to resolve, included.
        :param date_to: last night to resolve, included. Callers weighing
            ``closed_departure`` have to include the checkout night, which is
            the one it is expressed on.
        :param room_type_ids: optional room type ids to restrict to.
        :return: ``{(room_type_id, date): rule}``, with an entry only for the
            nights some rule covers. A night with no entry has no restriction.
        """
        date_from = fields.Date.to_date(date_from)
        date_to = fields.Date.to_date(date_to)
        domain = [
            ("availability_plan_id", "=", availability_plan_id),
            ("pms_property_id", "=", pms_property_id),
            ("date_from", "<=", date_to),
            ("date_to", ">=", date_from),
        ]
        if room_type_ids:
            domain.append(("room_type_id", "in", list(room_type_ids)))
        winner = {}
        # Sorting ascending and overwriting gives "last written wins" for
        # free. Sorted in Python because ``write_date`` is not indexed and the
        # recordset is a handful of rows once the ranges are in place.
        rules = self.search(domain).sorted(key=lambda rule: (rule.write_date, rule.id))
        for rule in rules:
            start = max(rule.date_from, date_from)
            end = min(rule.date_to, date_to)
            for offset in range((end - start).days + 1):
                key = (rule.room_type_id.id, start + datetime.timedelta(days=offset))
                winner[key] = rule
        return winner

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
