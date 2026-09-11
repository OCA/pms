# Copyright 2026 Commit [Sun]
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime

from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.osv import expression

# Scope levels. Their order is not a precedence: the effective value is the
# ``min`` across the levels that apply, never the most specific one.
LEVEL_GENERAL = "general"
LEVEL_SALE_CHANNEL = "sale_channel"
LEVEL_AGENCY = "agency"
LEVELS = (LEVEL_GENERAL, LEVEL_SALE_CHANNEL, LEVEL_AGENCY)

# ``-1`` is the stored sentinel for "no limit". Under ``min`` it would win
# over any real limit, so it is mapped to infinity while resolving.
NO_LIMIT = -1
INFINITE = float("inf")


def _as_limit(value):
    """Turn the stored value into something ``min`` can compare."""
    return INFINITE if value == NO_LIMIT else value


def _as_stored(value):
    """Turn a resolved limit back into the stored representation."""
    return NO_LIMIT if value == INFINITE else int(value)


def _level_of(rule):
    """Scope level of a rule, derived from its scope fields.

    Deliberately not a field: it adds no information, since the scope fields
    are mutually exclusive by constraint, and a stored compute would go stale
    on any write in raw SQL.
    """
    if rule.agency_id:
        return LEVEL_AGENCY
    if rule.sale_channel_id:
        return LEVEL_SALE_CHANNEL
    return LEVEL_GENERAL


class PmsInventoryRule(models.Model):
    """Commercial inventory put on sale, by date range and scope.

    How many rooms of a type the property puts on sale is a decision of the
    property and NOT of the rate plan, so this is kept apart from
    ``pms.availability.plan.rule``, which holds the restrictions that do
    depend on the rate.

    Purely declarative: nothing here derives from availability or from
    reservations. The resolution lives in ``get_inventory`` and
    ``get_inventory_caps``.

    INVARIANT: this model never reads ``pms.property.free_room_ids`` nor
    ``pms.property.availability``. It resolves declared caps only, and it is
    up to the caller to intersect them with physical availability. Breaking
    this creates an infinite recompute loop, since those fields call back into
    the resolver.
    """

    _name = "pms.inventory.rule"
    _description = "Commercial inventory rule by date range"
    _check_pms_properties_auto = True
    _order = "pms_property_id, room_type_id, date_from, write_date desc, id desc"

    pms_property_id = fields.Many2one(
        string="Property",
        help="Property the inventory rule belongs to",
        required=True,
        comodel_name="pms.property",
        ondelete="restrict",
        check_pms_properties=True,
    )
    room_type_id = fields.Many2one(
        string="Room Type",
        help="Room type whose inventory is limited by this rule",
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
    sale_channel_id = fields.Many2one(
        string="Sale Channel",
        help="If set, the rule only limits sales through this channel",
        index=True,
        comodel_name="pms.sale.channel",
        ondelete="cascade",
        check_pms_properties=True,
    )
    agency_id = fields.Many2one(
        string="Agency",
        help="If set, the rule only limits sales through this agency",
        index=True,
        comodel_name="res.partner",
        domain=[("is_agency", "=", True)],
        ondelete="cascade",
        check_pms_properties=True,
    )
    # NOTE: plain integers, not computes falling back to the room type
    # defaults: an explicit ``0`` means closed and has to survive. The
    # defaults are applied by the resolver, and only at the general level.
    quota = fields.Integer(
        help="Room nights that can be sold per night within this scope. "
        "Use -1 for no quota and 0 to close the scope.",
        default=NO_LIMIT,
    )
    max_avail = fields.Integer(
        string="Max. Availability",
        help="Maximum simultaneous availability shown within this scope. "
        "Use -1 for no limit and 0 to close the scope.",
        default=NO_LIMIT,
    )
    active = fields.Boolean(
        help="If unchecked, it will allow you to hide the "
        "inventory rule without removing it.",
        default=True,
    )

    # NOTE: overlapping rules of the same scope are legal and deliberately
    # left unconstrained: they are how a season is overridden for a shorter
    # period. The conflict is resolved when READING, last written wins.
    _sql_constraints = [
        (
            "date_range",
            "CHECK (date_to >= date_from)",
            "The last night of an inventory rule cannot be before the first one!",
        ),
        (
            "quota_not_below_no_limit",
            "CHECK (quota >= -1)",
            "Quota cannot be lower than -1, which already means no quota!",
        ),
        (
            "max_avail_not_below_no_limit",
            "CHECK (max_avail >= -1)",
            "Max. availability cannot be lower than -1, "
            "which already means no limit!",
        ),
        (
            "scope_exclusive",
            "CHECK (agency_id IS NULL OR sale_channel_id IS NULL)",
            "An inventory rule cannot be limited to a sale channel and to an "
            "agency at the same time!",
        ),
    ]

    def _auto_init(self):
        res = super()._auto_init()
        # The resolver always asks for one property over a window of dates,
        # and no single column index prunes that: ``date_from <= end`` holds
        # for every rule in the past, which is what accumulates. Hence
        # ``date_to`` first, the selective half.
        tools.create_index(
            self._cr,
            "pms_inventory_rule_property_date_index",
            self._table,
            ["pms_property_id", "date_to", "date_from"],
        )
        return res

    @api.constrains("agency_id")
    def _check_agency(self):
        for record in self.filtered("agency_id"):
            if not record.agency_id.is_agency:
                raise ValidationError(
                    _("The partner %s is not an agency") % record.agency_id.display_name
                )

    @api.model
    def collapse_dates(self, dates):
        """Group nights into the fewest ranges that cover them.

        The model expresses a period as one record, so any writer holding a
        set of nights with the same values has to collapse them before
        writing, or it lays down one rule per night.

        :param dates: an iterable of dates, in any order and with repeats.
        :return: a list of ``(date_from, date_to)`` tuples, both included.
        """
        ranges = []
        start = previous = None
        for date in sorted(set(dates)):
            if start is None:
                start = previous = date
            elif date == previous + datetime.timedelta(days=1):
                previous = date
            else:
                ranges.append((start, previous))
                start = previous = date
        if start is not None:
            ranges.append((start, previous))
        return ranges

    # Resolution

    @api.model
    def get_inventory(
        self,
        pms_property_id,
        date_from,
        date_to,
        room_type_ids=None,
        sale_channel_id=None,
        agency_id=None,
    ):
        """Resolve the declared inventory limits of a scope, night by night.

        Within the same level and scope, overlapping rules are resolved by
        last written wins. Across levels the effective value is the ``min``,
        with ``-1`` treated as infinite. When no general rule covers a
        (room type, night), the room type defaults are folded into the
        ``min``; the absence of a sale channel or agency rule contributes
        nothing.

        :param pms_property_id: id of the property to resolve for.
        :param date_from: first night to resolve, included.
        :param date_to: last night to resolve, included. Callers must not
            include the checkout night, which consumes no inventory.
        :param room_type_ids: optional room type ids to restrict to. Defaults
            to every room type with rooms in the property.
        :param sale_channel_id: optional ``pms.sale.channel`` id, to take the
            sale channel level into account.
        :param agency_id: optional agency id, to take the agency level into
            account.
        :return: ``{(room_type_id, date): {"quota": int, "max_avail": int}}``
            with an entry for every requested (room type, night) and ``-1``
            keeping its meaning of "no limit".
        """
        winner = self._resolve_rules(
            pms_property_id,
            date_from,
            date_to,
            room_type_ids=room_type_ids,
            sale_channel_id=sale_channel_id,
            agency_id=agency_id,
        )
        inventory = {}
        for room_type, date, rules, general in self._iter_resolved(
            winner, pms_property_id, date_from, date_to, room_type_ids=room_type_ids
        ):
            quota = max_avail = INFINITE
            for rule in rules.values():
                quota = min(quota, _as_limit(rule.quota))
                max_avail = min(max_avail, _as_limit(rule.max_avail))
            if not general:
                # The room type defaults are the fallback of the GENERAL
                # level only: most of them are set to ``0`` and it is the
                # rules that open the sale, so folding them in for a missing
                # channel or agency rule would close every channel.
                quota = min(quota, _as_limit(room_type.default_quota))
                max_avail = min(max_avail, _as_limit(room_type.default_max_avail))
            inventory[(room_type.id, date)] = {
                "quota": _as_stored(quota),
                "max_avail": _as_stored(max_avail),
            }
        return inventory

    @api.model
    def get_inventory_caps(
        self,
        pms_property_id,
        date_from,
        date_to,
        room_type_ids=None,
        sale_channel_id=None,
        agency_id=None,
    ):
        """Bookable cap declared for a scope, night by night.

        Folds ``max_avail``, an exposure cap, with the quota left to sell.
        The two behave differently on purpose: reservations already made are
        reflected in ``pms.availability.real_avail``, so subtracting them from
        ``max_avail`` would count them twice, while ``quota`` is an allowance
        and what is left of it is the cap minus what the scope already sold.

        The ``min`` across levels is applied to the REMAINING quota, not to
        the cap: the winning quota may come from a level other than the one
        the consumption belongs to.

        Arguments are those of :meth:`get_inventory`.

        :return: ``{(room_type_id, date): int or None}`` where ``None`` means
            no cap at all and ``0`` means closed. The caller is responsible
            for intersecting the result with physical availability.
        """
        winner = self._resolve_rules(
            pms_property_id,
            date_from,
            date_to,
            room_type_ids=room_type_ids,
            sale_channel_id=sale_channel_id,
            agency_id=agency_id,
        )
        room_types = self._get_scoped_room_types(pms_property_id, room_type_ids)
        # The count aggregates over ``pms.reservation.line``, a big table.
        # Only ``quota`` is an allowance, so with no quota in play anywhere
        # there is nothing to count.
        quota_in_play = any(
            rule.quota != NO_LIMIT for rule in set(winner.values())
        ) or any(room_type.default_quota != NO_LIMIT for room_type in room_types)
        consumption = (
            self._get_quota_consumption(
                pms_property_id,
                date_from,
                date_to,
                room_type_ids=room_type_ids,
                sale_channel_id=sale_channel_id,
                agency_id=agency_id,
            )
            if quota_in_play
            else {}
        )
        caps = {}
        for room_type, date, rules, general in self._iter_resolved(
            winner,
            pms_property_id,
            date_from,
            date_to,
            room_type_ids=room_type_ids,
            room_types=room_types,
        ):
            cap = INFINITE
            for level, rule in rules.items():
                cap = min(cap, _as_limit(rule.max_avail))
                if rule.quota != NO_LIMIT:
                    consumed = consumption.get((level, room_type.id, date), 0)
                    cap = min(cap, rule.quota - consumed)
            if not general:
                cap = min(cap, _as_limit(room_type.default_max_avail))
                if room_type.default_quota != NO_LIMIT:
                    consumed = consumption.get((LEVEL_GENERAL, room_type.id, date), 0)
                    cap = min(cap, room_type.default_quota - consumed)
            caps[(room_type.id, date)] = None if cap == INFINITE else max(0, int(cap))
        return caps

    @api.model
    def _get_quota_consumption(
        self,
        pms_property_id,
        date_from,
        date_to,
        room_type_ids=None,
        sale_channel_id=None,
        agency_id=None,
    ):
        """Count the room nights already sold within a scope.

        Counts by the room type SOLD (``reservation_id.room_type_id``), not by
        the room type of the room finally assigned: on an upgrade the quota
        spent belongs to what was sold.

        There is NO state filter, and that is the point: a quota of 5 for an
        agency means "I want to sell 5 through it", and a cancelled night was
        sold all the same. Cancelling does not give the quota back. Note this
        is deliberately NOT the predicate ``pms.availability.real_avail``
        uses, which does free a cancelled night: the two measure different
        things, physical occupancy against what an allowance has spent.

        It is also what the counter this replaces did. ``update_quota`` fired
        on the line ``create`` without looking at any state, and never gave
        anything back.

        :return: ``{(level, room_type_id, date): consumed}``, with an entry
            only for the levels implied by the arguments and for the keys that
            actually consumed something.
        """
        date_from = fields.Date.to_date(date_from)
        date_to = fields.Date.to_date(date_to)
        domain = [
            ("pms_property_id", "=", pms_property_id),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
        ]
        if room_type_ids:
            domain.append(("reservation_id.room_type_id", "in", list(room_type_ids)))
        scopes = [(LEVEL_GENERAL, [])]
        if sale_channel_id:
            scopes.append(
                (
                    LEVEL_SALE_CHANNEL,
                    [("sale_channel_id", "=", sale_channel_id)],
                )
            )
        if agency_id:
            scopes.append(
                (LEVEL_AGENCY, [("reservation_id.agency_id", "=", agency_id)])
            )
        ReservationLine = self.env["pms.reservation.line"].sudo()
        consumption = {}
        for level, scope_domain in scopes:
            # Odoo cannot group by a dotted path, so the sold room type is
            # resolved from the reservation in a second, single query.
            groups = ReservationLine.read_group(
                expression.AND([domain, scope_domain]),
                ["__count"],
                ["date:day", "reservation_id"],
                lazy=False,
            )
            if not groups:
                continue
            reservation_ids = [
                group["reservation_id"][0]
                for group in groups
                if group["reservation_id"]
            ]
            reservations = (
                self.env["pms.reservation"].sudo().browse(set(reservation_ids))
            )
            sold_room_type = {
                reservation.id: reservation.room_type_id.id
                for reservation in reservations
            }
            for group in groups:
                if not group["reservation_id"]:
                    continue
                room_type_id = sold_room_type.get(group["reservation_id"][0])
                if not room_type_id:
                    continue
                # Use the ISO ``__range`` boundary: the ``date:day`` label is
                # locale-formatted and cannot be parsed reliably.
                date = fields.Date.to_date(group["__range"]["date:day"]["from"])
                key = (level, room_type_id, date)
                consumption[key] = consumption.get(key, 0) + group["__count"]
        return consumption

    @api.model
    def _resolve_rules(
        self,
        pms_property_id,
        date_from,
        date_to,
        room_type_ids=None,
        sale_channel_id=None,
        agency_id=None,
    ):
        """Expand the rules of a scope into the winner of every night.

        :return: ``{(level, room_type_id, date): rule}`` holding, for every
            level and night covered by a rule, the rule that wins.
        """
        date_from = fields.Date.to_date(date_from)
        date_to = fields.Date.to_date(date_to)
        domain = [
            ("pms_property_id", "=", pms_property_id),
            ("date_from", "<=", date_to),
            ("date_to", ">=", date_from),
        ]
        if room_type_ids:
            domain.append(("room_type_id", "in", list(room_type_ids)))
        # Filtered positively: rules of other channels or agencies never
        # apply, so they are not even fetched. A scope field set excludes the
        # other by constraint, so each clause pins a single level.
        scope_domain = [
            ("sale_channel_id", "=", False),
            ("agency_id", "=", False),
        ]
        if sale_channel_id:
            scope_domain = expression.OR(
                [scope_domain, [("sale_channel_id", "=", sale_channel_id)]]
            )
        if agency_id:
            scope_domain = expression.OR(
                [scope_domain, [("agency_id", "=", agency_id)]]
            )
        # ``sudo`` mirrors the availability computes: the portal and API
        # paths resolve without revenue management rights, and the property is
        # already pinned in the domain. ``active_test`` is pinned so that an
        # archived rule never applies, whatever the caller carries.
        rules = (
            self.sudo()
            .with_context(active_test=True)
            .search(expression.AND([domain, scope_domain]))
        )
        winner = {}
        # Sorting ascending and overwriting gives "last written wins" for
        # free. Sorted in Python because ``write_date`` is not indexed and the
        # recordset is a handful of rows once the ranges are in place.
        for rule in rules.sorted(key=lambda r: (r.write_date, r.id)):
            start = max(rule.date_from, date_from)
            end = min(rule.date_to, date_to)
            for offset in range((end - start).days + 1):
                key = (
                    _level_of(rule),
                    rule.room_type_id.id,
                    start + datetime.timedelta(days=offset),
                )
                winner[key] = rule
        return winner

    @api.model
    def _get_scoped_room_types(self, pms_property_id, room_type_ids=None):
        """Room types to resolve for, defaulting to those of the property."""
        if room_type_ids:
            return self.env["pms.room.type"].browse(list(room_type_ids))
        return (
            self.env["pms.property"]
            .browse(pms_property_id)
            .room_ids.mapped("room_type_id")
        )

    @api.model
    def _iter_resolved(
        self,
        winner,
        pms_property_id,
        date_from,
        date_to,
        room_type_ids=None,
        room_types=None,
    ):
        """Yield the rules that apply to every (room type, night) of a scope.

        :param winner: the expansion returned by :meth:`_resolve_rules`.
        :param room_types: optional recordset, to avoid resolving the room
            types of the property twice.
        :return: an iterator of ``(room_type, date, rules, general)`` where
            ``rules`` maps each level with a winning rule to that rule, and
            ``general`` tells whether the general level is covered, which is
            what decides if the room type defaults come into play.
        """
        date_from = fields.Date.to_date(date_from)
        date_to = fields.Date.to_date(date_to)
        if room_types is None:
            room_types = self._get_scoped_room_types(pms_property_id, room_type_ids)
        for offset in range((date_to - date_from).days + 1):
            date = date_from + datetime.timedelta(days=offset)
            for room_type in room_types:
                rules = {}
                for level in LEVELS:
                    rule = winner.get((level, room_type.id, date))
                    if rule:
                        rules[level] = rule
                yield room_type, date, rules, LEVEL_GENERAL in rules
