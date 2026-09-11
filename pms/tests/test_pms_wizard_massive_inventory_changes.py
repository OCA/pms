import datetime

from odoo import fields
from odoo.exceptions import UserError

from .common import TestPms


class TestPmsInventoryMassiveChanges(TestPms):
    """Cover the bulk creation of inventory rules.

    What is worth testing here is the shape of what the wizard produces: how
    many rules, over which ranges, and with which values. The resolution of
    those rules is covered in ``test_pms_inventory_rule``.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.today()
        cls.pricelist_test = cls.env["product.pricelist"].create(
            {
                "name": "Massive inventory pricelist",
                "availability_plan_id": cls.availability_plan1.id,
                "is_pms_available": True,
            }
        )
        cls.property_a = cls.env["pms.property"].create(
            {
                "name": "Massive inventory property A",
                "company_id": cls.company1.id,
                "default_pricelist_id": cls.pricelist_test.id,
            }
        )
        cls.property_b = cls.env["pms.property"].create(
            {
                "name": "Massive inventory property B",
                "company_id": cls.company1.id,
                "default_pricelist_id": cls.pricelist_test.id,
            }
        )
        cls.room_type_a = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [(4, cls.property_a.id)],
                "name": "Only in A",
                "default_code": "ONLYA",
                "class_id": cls.room_type_class1.id,
                "default_quota": 7,
                "default_max_avail": 4,
            }
        )
        cls.room_type_shared = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [
                    (4, cls.property_a.id),
                    (4, cls.property_b.id),
                ],
                "name": "In both",
                "default_code": "BOTH",
                "class_id": cls.room_type_class1.id,
                "default_quota": 7,
                "default_max_avail": 4,
            }
        )
        cls.channel = cls.env["pms.sale.channel"].create(
            {"name": "Massive channel", "channel_type": "indirect"}
        )
        cls.agency = cls.env["res.partner"].create(
            {
                "name": "Massive agency",
                "is_agency": True,
                "sale_channel_id": cls.channel.id,
                "property_product_pricelist": cls.pricelist_test.id,
            }
        )

    def _wizard(self, **values):
        return self.env["pms.inventory.massive.changes.wizard"].create(
            dict(
                {
                    "pms_property_ids": [(6, 0, self.property_a.ids)],
                    "room_type_ids": [(6, 0, self.room_type_a.ids)],
                    "date_from": self.today,
                    "date_to": self.today + datetime.timedelta(days=6),
                    "apply_quota": True,
                    "quota": 3,
                },
                **values,
            )
        )

    def _rules(self):
        """Only the rules of the test properties.

        The demo data of the module ships inventory rules of its own, so an
        unscoped search would count those too.
        """
        return self.env["pms.inventory.rule"].search(
            [("pms_property_id", "in", (self.property_a + self.property_b).ids)]
        )

    def test_all_week_creates_a_single_range(self):
        """
        A whole week with no day filter is one rule covering the range, not
        one rule per day.
        """
        self._wizard().apply_inventory_changes()

        rules = self._rules()
        self.assertEqual(len(rules), 1, "The whole period must be a single rule")
        self.assertEqual(rules.date_from, self.today)
        self.assertEqual(rules.date_to, self.today + datetime.timedelta(days=6))
        self.assertEqual(rules.quota, 3)

    def test_consecutive_days_are_grouped(self):
        """
        Selecting the weekend of a period yields one rule per weekend, with
        the two nights grouped, instead of one rule per day.
        """
        # A three week window starting on a Monday, to make the weekends
        # predictable whatever day the test runs on.
        monday = self.today + datetime.timedelta(days=(7 - self.today.weekday()) % 7)
        wizard = self._wizard(
            date_from=monday,
            date_to=monday + datetime.timedelta(days=20),
            apply_on_all_week=False,
            apply_on_saturday=True,
            apply_on_sunday=True,
        )

        wizard.apply_inventory_changes()

        rules = self._rules()
        self.assertEqual(len(rules), 3, "One rule per weekend of the period")
        for rule in rules:
            self.assertEqual(
                (rule.date_to - rule.date_from).days,
                1,
                "Saturday and Sunday must be grouped in the same rule",
            )
            self.assertEqual(rule.date_from.weekday(), 5, "Must start on Saturday")

    def test_non_consecutive_days_are_not_grouped(self):
        """
        A day filter that leaves gaps produces one rule per isolated day.
        """
        monday = self.today + datetime.timedelta(days=(7 - self.today.weekday()) % 7)
        wizard = self._wizard(
            date_from=monday,
            date_to=monday + datetime.timedelta(days=6),
            apply_on_all_week=False,
            apply_on_monday=True,
            apply_on_wednesday=True,
        )

        wizard.apply_inventory_changes()

        rules = self._rules()
        self.assertEqual(len(rules), 2)
        for rule in rules:
            self.assertEqual(rule.date_from, rule.date_to, "One night each")

    def test_the_value_not_applied_keeps_the_room_type_default(self):
        """
        Applying only the quota must not lift the max availability the room
        type defaults to.

        A general rule replaces the room type defaults in BOTH fields, so
        writing -1 in the one left out would put on sale what the room type
        keeps closed.
        """
        self._wizard(apply_quota=True, quota=3).apply_inventory_changes()

        rule = self._rules()
        self.assertEqual(rule.quota, 3, "The applied value must be the one given")
        self.assertEqual(
            rule.max_avail,
            self.room_type_a.default_max_avail,
            "The value not applied must keep the room type default",
        )

    def test_scope_is_carried_to_the_rules(self):
        """
        The scope chosen ends up on the rules.
        """
        self._wizard(level="agency", agency_id=self.agency.id).apply_inventory_changes()

        rule = self._rules()
        self.assertEqual(rule.agency_id, self.agency)
        self.assertFalse(rule.sale_channel_id)

    def test_room_type_not_in_the_property_is_skipped(self):
        """
        A room type that is not available in a property is skipped for it,
        instead of failing the whole bulk change.
        """
        self._wizard(
            pms_property_ids=[(6, 0, (self.property_a + self.property_b).ids)],
            room_type_ids=[(6, 0, (self.room_type_a + self.room_type_shared).ids)],
        ).apply_inventory_changes()

        rules = self._rules()
        self.assertEqual(len(rules), 3, "Both types in A, only the shared one in B")
        self.assertEqual(
            rules.filtered(
                lambda rule, prop=self.property_b: rule.pms_property_id == prop
            ).room_type_id,
            self.room_type_shared,
        )

    def test_every_room_type_when_none_given(self):
        """
        With no room type given, the rules cover every room type of the
        properties.
        """
        self._wizard(room_type_ids=[(5, 0, 0)]).apply_inventory_changes()

        rules = self._rules()
        self.assertIn(self.room_type_a, rules.room_type_id)
        self.assertIn(self.room_type_shared, rules.room_type_id)

    def test_nothing_to_apply_is_rejected(self):
        """
        The wizard refuses to create rules with neither value applied.
        """
        with self.assertRaises(UserError):
            self._wizard(
                apply_quota=False, apply_max_avail=False
            ).apply_inventory_changes()

    def test_a_period_without_matching_days_is_rejected(self):
        """
        A day filter matching no day of the period is refused instead of
        silently creating nothing.
        """
        monday = self.today + datetime.timedelta(days=(7 - self.today.weekday()) % 7)
        with self.assertRaises(UserError):
            self._wizard(
                date_from=monday,
                date_to=monday + datetime.timedelta(days=1),
                apply_on_all_week=False,
                apply_on_saturday=True,
            ).apply_inventory_changes()

    def test_scope_without_its_record_is_rejected(self):
        """
        Choosing a scope without the channel or the agency it needs is
        refused.
        """
        with self.assertRaises(UserError):
            self._wizard(level="sale_channel").apply_inventory_changes()

    def test_repeating_the_change_rewrites_the_rule(self):
        """
        Applying the same scope over the same period does not stack a second
        rule, it rewrites the one already there.
        """
        self._wizard(quota=3).apply_inventory_changes()
        self._wizard(quota=5).apply_inventory_changes()

        rules = self._rules()
        self.assertEqual(len(rules), 1, "The rule must be rewritten, not duplicated")
        self.assertEqual(rules.quota, 5, "The last value applied must be the one kept")

    def test_a_different_period_is_a_new_rule(self):
        """
        A period that only overlaps the rule already there leaves it alone and
        creates its own, which is how an override is expressed.
        """
        self._wizard(quota=3).apply_inventory_changes()
        self._wizard(
            date_from=self.today + datetime.timedelta(days=3),
            date_to=self.today + datetime.timedelta(days=9),
            quota=5,
        ).apply_inventory_changes()

        rules = self._rules()
        self.assertEqual(len(rules), 2)
        self.assertEqual(
            rules.filtered(lambda rule: rule.quota == 3).date_from, self.today
        )

    def test_a_different_scope_is_a_new_rule(self):
        """
        The same period on another scope is another rule: rewriting would
        silently move the inventory of the first scope.
        """
        self._wizard(quota=3).apply_inventory_changes()
        self._wizard(
            level="agency", agency_id=self.agency.id, quota=5
        ).apply_inventory_changes()

        rules = self._rules()
        self.assertEqual(len(rules), 2)
        self.assertEqual(
            rules.filtered(lambda rule: not rule.agency_id).quota,
            3,
            "The general rule must keep its own quota",
        )

    def test_an_archived_rule_is_not_rewritten(self):
        """
        A rule hidden on purpose is not brought back to life by a bulk change.
        """
        self._wizard(quota=3).apply_inventory_changes()
        archived = self._rules()
        archived.active = False

        self._wizard(quota=5).apply_inventory_changes()

        self.assertFalse(archived.active, "The archived rule must stay archived")
        self.assertEqual(archived.quota, 3, "The archived rule must not be rewritten")
        self.assertEqual(
            self._rules().quota, 5, "A new rule must carry the value applied"
        )
