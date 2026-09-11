# Copyright 2026 Commit [Sun]
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError

WEEK_DAY_FIELDS = (
    "apply_on_monday",
    "apply_on_tuesday",
    "apply_on_wednesday",
    "apply_on_thursday",
    "apply_on_friday",
    "apply_on_saturday",
    "apply_on_sunday",
)


class PmsInventoryMassiveChangesWizard(models.TransientModel):
    """Create inventory rules in bulk.

    A single ``pms.inventory.rule`` already covers a whole season, so this is
    not the per-day generator the availability plan rules need: it exists for
    the other two axes, several properties and room types at once, and for the
    days of the week, which the rule itself does not model.

    A bulk change rewrites the rule already there when it would be an exact
    duplicate of it, and creates one otherwise. It never touches a rule that
    merely overlaps, and never deletes: laying a new layer on top is how an
    override is expressed.
    """

    _name = "pms.inventory.massive.changes.wizard"
    _description = "Wizard for massive changes on the commercial inventory"
    _check_pms_properties_auto = True

    pms_property_ids = fields.Many2many(
        string="Properties",
        comodel_name="pms.property",
        required=True,
        check_pms_properties=True,
    )
    room_type_ids = fields.Many2many(
        string="Room Types",
        help="Room types to create the rules for. "
        "If empty, every room type of the properties given.",
        comodel_name="pms.room.type",
        check_pms_properties=True,
    )
    date_from = fields.Date(
        string="From",
        required=True,
    )
    date_to = fields.Date(
        string="To",
        required=True,
    )
    apply_on_monday = fields.Boolean(string="Mondays", default=False)
    apply_on_tuesday = fields.Boolean(string="Tuesdays", default=False)
    apply_on_wednesday = fields.Boolean(string="Wednesdays", default=False)
    apply_on_thursday = fields.Boolean(string="Thursdays", default=False)
    apply_on_friday = fields.Boolean(string="Fridays", default=False)
    apply_on_saturday = fields.Boolean(string="Saturdays", default=False)
    apply_on_sunday = fields.Boolean(string="Sundays", default=False)
    apply_on_all_week = fields.Boolean(
        string="Apply all week",
        default=True,
    )
    level = fields.Selection(
        string="Scope",
        help="Scope the rules will be limited to",
        selection=[
            ("general", "General"),
            ("sale_channel", "Sale Channel"),
            ("agency", "Agency"),
        ],
        default="general",
        required=True,
    )
    sale_channel_id = fields.Many2one(
        string="Sale Channel",
        comodel_name="pms.sale.channel",
        check_pms_properties=True,
    )
    agency_id = fields.Many2one(
        string="Agency",
        comodel_name="res.partner",
        domain=[("is_agency", "=", True)],
        check_pms_properties=True,
    )
    apply_quota = fields.Boolean(string="Apply changes to Quota", default=False)
    quota = fields.Integer(
        help="Room nights that can be sold per night within the scope. "
        "Use -1 for no quota and 0 to close the scope.",
        default=-1,
    )
    apply_max_avail = fields.Boolean(
        string="Apply changes to Max. Avail.", default=False
    )
    max_avail = fields.Integer(
        string="Max. Availability",
        help="Maximum simultaneous availability shown within the scope. "
        "Use -1 for no limit and 0 to close the scope.",
        default=-1,
    )

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for record in self:
            if record.date_to < record.date_from:
                raise UserError(_("The end date cannot be before the start date"))

    def _get_date_ranges(self):
        """Group the days matching the weekday filter into ranges.

        Consecutive days are collapsed, so "weekends of the season" yields one
        two night rule per weekend instead of two rules per day.

        :return: a list of ``(date_from, date_to)`` tuples, both included.
        """
        self.ensure_one()
        week_days = tuple(self[field] for field in WEEK_DAY_FIELDS)
        dates = []
        for offset in range((self.date_to - self.date_from).days + 1):
            date = self.date_from + datetime.timedelta(days=offset)
            if self.apply_on_all_week or week_days[date.weekday()]:
                dates.append(date)
        return self.env["pms.inventory.rule"].collapse_dates(dates)

    def _get_room_types(self, pms_property):
        """Room types to create rules for in a property.

        A room type not available in the property is skipped rather than
        rejected: the multi property check would raise halfway through an
        otherwise valid bulk change.
        """
        self.ensure_one()
        if self.room_type_ids:
            return self.room_type_ids.filtered(
                lambda room_type, prop=pms_property: not room_type.pms_property_ids
                or prop in room_type.pms_property_ids
            )
        return self.env["pms.room.type"].search(
            [
                "|",
                ("pms_property_ids", "=", False),
                ("pms_property_ids", "in", pms_property.ids),
            ]
        )

    def _get_scope(self):
        """The scope fields the rules will carry, from the level chosen.

        :return: a dict ready to be written on ``pms.inventory.rule``.
        """
        self.ensure_one()
        if self.level == "sale_channel":
            if not self.sale_channel_id:
                raise UserError(_("Choose the sale channel to limit the rules to"))
            return {"sale_channel_id": self.sale_channel_id.id}
        if self.level == "agency":
            if not self.agency_id:
                raise UserError(_("Choose the agency to limit the rules to"))
            return {"agency_id": self.agency_id.id}
        return {}

    def _get_rules_to_rewrite(self, date_ranges, scope):
        """Rules already there that this bulk change would duplicate.

        Only an EXACT match is reused: same property, same room type, same
        scope and the same two dates. A rule that merely overlaps is left
        alone, because narrowing it would change what was configured outside
        the period asked for, and laying a new rule on top of it is precisely
        how an override is expressed.

        Archived rules are not reused either, so a bulk change does not bring
        back to life a rule that was hidden on purpose.

        When several rules share the same key, from bulk changes made before
        this reuse existed, the one rewritten is the one that resolves today,
        the last written. The others stay fully shadowed by it.

        :return: ``{(property_id, room_type_id, date_from, date_to): rule}``
        """
        self.ensure_one()
        domain = [
            ("pms_property_id", "in", self.pms_property_ids.ids),
            ("date_from", "in", [dates[0] for dates in date_ranges]),
            ("date_to", "in", [dates[1] for dates in date_ranges]),
        ]
        if self.room_type_ids:
            domain.append(("room_type_id", "in", self.room_type_ids.ids))
        # Both scope fields are pinned, the unused one to empty, so a rule of
        # a different scope is never taken for a match.
        domain += [
            (field, "=", scope.get(field, False))
            for field in ("sale_channel_id", "agency_id")
        ]
        rules = self.env["pms.inventory.rule"].search(domain)
        return {
            (
                rule.pms_property_id.id,
                rule.room_type_id.id,
                rule.date_from,
                rule.date_to,
            ): rule
            for rule in rules.sorted(key=lambda rule: (rule.write_date, rule.id))
        }

    def apply_inventory_changes(self):
        self.ensure_one()
        if not self.apply_quota and not self.apply_max_avail:
            raise UserError(_("Set the quota, the maximum availability or both"))
        date_ranges = self._get_date_ranges()
        if not date_ranges:
            raise UserError(
                _("No day in the period matches the days of the week selected")
            )
        scope = self._get_scope()
        to_rewrite = self._get_rules_to_rewrite(date_ranges, scope)

        InventoryRule = self.env["pms.inventory.rule"]
        applied = InventoryRule
        for pms_property in self.pms_property_ids:
            for room_type in self._get_room_types(pms_property):
                # The field left out keeps the CURRENT default of the room
                # type, not -1: a general rule replaces the defaults in BOTH
                # fields, so a -1 would lift a closing default.
                inventory = {
                    "quota": self.quota
                    if self.apply_quota
                    else room_type.default_quota,
                    "max_avail": self.max_avail
                    if self.apply_max_avail
                    else room_type.default_max_avail,
                }
                for dates in date_ranges:
                    rule = to_rewrite.get((pms_property.id, room_type.id) + dates)
                    if rule:
                        # Same result as stacking another identical rule, one
                        # row less: the write bumps ``write_date``, so it
                        # still wins any overlap.
                        rule.write(inventory)
                    else:
                        rule = InventoryRule.create(
                            dict(
                                inventory,
                                **scope,
                                pms_property_id=pms_property.id,
                                room_type_id=room_type.id,
                                date_from=dates[0],
                                date_to=dates[1],
                            )
                        )
                    applied |= rule
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "pms.pms_inventory_rule_action"
        )
        action["domain"] = [("id", "in", applied.ids)]
        action["context"] = dict(self.env.context, search_default_future=0)
        return action
