# Copyright 2026 Commit [Sun]
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""A plan can fall back to another one.

The child carries only the nights it changes; for the rest the parent's rules
apply, and so on up the chain.
"""
import datetime

from odoo.exceptions import ValidationError

from .common import TestPms


class TestPmsAvailabilityPlanInheritance(TestPms):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = datetime.date.today()
        cls.room_type = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Inheritance Double",
                "default_code": "INHD",
                "class_id": cls.room_type_class1.id,
                "list_price": 25,
            }
        )
        cls.parent = cls.env["pms.availability.plan"].create({"name": "General"})
        cls.child = cls.env["pms.availability.plan"].create(
            {"name": "OTA", "parent_id": cls.parent.id}
        )

    def _rule(self, plan, day_from, day_to, **values):
        return self.env["pms.availability.plan.rule"].create(
            {
                "availability_plan_id": plan.id,
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type.id,
                "date_from": self.today + datetime.timedelta(days=day_from),
                "date_to": self.today + datetime.timedelta(days=day_to),
                **values,
            }
        )

    def _resolve(self, plan, day_from, day_to):
        return self.env["pms.availability.plan.rule"]._resolve_rules(
            plan.id,
            self.pms_property1.id,
            self.today + datetime.timedelta(days=day_from),
            self.today + datetime.timedelta(days=day_to),
        )

    def _night(self, winner, day):
        return winner.get(
            (self.room_type.id, self.today + datetime.timedelta(days=day))
        )

    def test_child_falls_back_to_the_parent(self):
        self._rule(self.parent, 1, 5, min_stay=3)
        winner = self._resolve(self.child, 1, 5)
        self.assertEqual(len(winner), 5)
        self.assertEqual({rule.min_stay for rule in winner.values()}, {3})

    def test_the_child_wins_where_it_has_a_rule(self):
        self._rule(self.parent, 1, 5, min_stay=3)
        self._rule(self.child, 2, 3, min_stay=7)
        winner = self._resolve(self.child, 1, 5)
        self.assertEqual(self._night(winner, 1).min_stay, 3)
        self.assertEqual(self._night(winner, 2).min_stay, 7)
        self.assertEqual(self._night(winner, 3).min_stay, 7)
        self.assertEqual(self._night(winner, 4).min_stay, 3)

    def test_the_child_can_open_what_the_parent_closes(self):
        """The whole rule is replaced, so a child rule saying ``closed``
        is False beats a parent that closes the night."""
        self._rule(self.parent, 1, 5, closed=True)
        self._rule(self.child, 3, 3, closed=False)
        winner = self._resolve(self.child, 1, 5)
        self.assertTrue(self._night(winner, 2).closed)
        self.assertFalse(self._night(winner, 3).closed)

    def test_the_child_rule_replaces_the_parent_one_whole(self):
        """No field level merging: what the child does not restate is gone,
        because 0 and False are values in their own right."""
        self._rule(self.parent, 1, 5, min_stay=3, closed_arrival=True)
        self._rule(self.child, 2, 2, min_stay=7)
        night = self._night(self._resolve(self.child, 1, 5), 2)
        self.assertEqual(night.min_stay, 7)
        self.assertFalse(night.closed_arrival)

    def test_editing_the_parent_does_not_beat_the_child(self):
        """THE regression to guard: if depth were folded into the same
        criterion as ``write_date``, touching the general plan would take
        over the nights the child overrides.

        The parent is aged by hand because Odoo stamps every write of a
        transaction with the same ``write_date``, so editing it here would
        not make it any more recent than the child.
        """
        parent_rule = self._rule(self.parent, 1, 5, min_stay=3)
        child_rule = self._rule(self.child, 2, 3, min_stay=7)
        self.env.cr.execute(
            "UPDATE pms_availability_plan_rule "
            "SET write_date = write_date + interval '1 day' WHERE id = %s",
            (parent_rule.id,),
        )
        parent_rule.invalidate_recordset(["write_date"])
        self.assertGreater(parent_rule.write_date, child_rule.write_date)
        winner = self._resolve(self.child, 1, 5)
        self.assertEqual(self._night(winner, 1).min_stay, 3)
        self.assertEqual(self._night(winner, 2).min_stay, 7)

    def test_the_chain_goes_deeper_than_one_level(self):
        grandchild = self.env["pms.availability.plan"].create(
            {"name": "OTA Sale", "parent_id": self.child.id}
        )
        self._rule(self.parent, 1, 5, min_stay=3)
        self._rule(self.child, 1, 4, min_stay=7)
        self._rule(grandchild, 1, 2, min_stay=9)
        winner = self._resolve(grandchild, 1, 5)
        self.assertEqual(self._night(winner, 1).min_stay, 9)
        self.assertEqual(self._night(winner, 3).min_stay, 7)
        self.assertEqual(self._night(winner, 5).min_stay, 3)

    def test_the_parent_does_not_see_the_child(self):
        self._rule(self.child, 1, 5, min_stay=7)
        self.assertFalse(self._resolve(self.parent, 1, 5))

    def test_a_rule_of_another_property_is_not_inherited(self):
        pms_property2 = self.env["pms.property"].create(
            {
                "name": "Inheritance Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        self.room_type.pms_property_ids = [(4, pms_property2.id)]
        self.env["pms.availability.plan.rule"].create(
            {
                "availability_plan_id": self.parent.id,
                "pms_property_id": pms_property2.id,
                "room_type_id": self.room_type.id,
                "date_from": self.today + datetime.timedelta(days=1),
                "date_to": self.today + datetime.timedelta(days=5),
                "min_stay": 3,
            }
        )
        self.assertFalse(self._resolve(self.child, 1, 5))

    def test_a_plan_cannot_inherit_from_itself(self):
        with self.assertRaises(ValidationError):
            self.parent.parent_id = self.parent

    def test_the_chain_cannot_close_on_itself(self):
        with self.assertRaises(ValidationError):
            self.parent.parent_id = self.child
