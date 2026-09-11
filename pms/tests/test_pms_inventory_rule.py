import datetime

from psycopg2 import IntegrityError

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tools import mute_logger

from .common import TestPms


class TestPmsInventoryRule(TestPms):
    """Cover the resolution of ``pms.inventory.rule``.

    Everything worth testing in this model lives in the resolver, so the tests
    call ``get_inventory`` and ``get_inventory_caps`` directly instead of going
    through ``pms.property.availability``: at this point nothing in ``pms``
    consumes the model yet.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.today = fields.Date.today()
        cls.tomorrow = cls.today + datetime.timedelta(days=1)

        cls.pricelist_test = cls.env["product.pricelist"].create(
            {
                "name": "Inventory rule pricelist",
                "availability_plan_id": cls.availability_plan1.id,
                "is_pms_available": True,
            }
        )
        cls.property_test = cls.env["pms.property"].create(
            {
                "name": "Inventory rule property",
                "company_id": cls.company1.id,
                "default_pricelist_id": cls.pricelist_test.id,
            }
        )
        cls.pricelist_test.pms_property_ids = [(4, cls.property_test.id)]

        cls.room_type_double = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [(4, cls.property_test.id)],
                "name": "Double inventory",
                "default_code": "DBL_INV",
                "class_id": cls.room_type_class1.id,
            }
        )
        cls.room_type_single = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [(4, cls.property_test.id)],
                "name": "Single inventory",
                "default_code": "SNG_INV",
                "class_id": cls.room_type_class1.id,
            }
        )
        for number in (201, 202, 203):
            cls.env["pms.room"].create(
                {
                    "pms_property_id": cls.property_test.id,
                    "name": "Double %s" % number,
                    "room_type_id": cls.room_type_double.id,
                    "capacity": 2,
                }
            )
        cls.env["pms.room"].create(
            {
                "pms_property_id": cls.property_test.id,
                "name": "Single 101",
                "room_type_id": cls.room_type_single.id,
                "capacity": 1,
            }
        )

        cls.channel_a = cls.env["pms.sale.channel"].create(
            {"name": "Channel A", "channel_type": "direct"}
        )
        cls.channel_b = cls.env["pms.sale.channel"].create(
            {"name": "Channel B", "channel_type": "direct"}
        )
        cls.channel_indirect = cls.env["pms.sale.channel"].create(
            {"name": "Indirect", "channel_type": "indirect"}
        )
        cls.agency_a = cls.env["res.partner"].create(
            {
                "name": "Agency A",
                "is_agency": True,
                "sale_channel_id": cls.channel_indirect.id,
                "property_product_pricelist": cls.pricelist_test.id,
            }
        )
        cls.agency_b = cls.env["res.partner"].create(
            {
                "name": "Agency B",
                "is_agency": True,
                "sale_channel_id": cls.channel_indirect.id,
                "property_product_pricelist": cls.pricelist_test.id,
            }
        )
        cls.guest = cls.env["res.partner"].create(
            {"name": "Guest", "property_product_pricelist": cls.pricelist_test.id}
        )

    # Helpers

    def _rule(self, **values):
        """Create an inventory rule for the test property and the double."""
        return self.env["pms.inventory.rule"].create(
            dict(
                {
                    "pms_property_id": self.property_test.id,
                    "room_type_id": self.room_type_double.id,
                    "date_from": self.today,
                    "date_to": self.today,
                },
                **values,
            )
        )

    def _inventory(self, date_from=None, date_to=None, **scope):
        return self.env["pms.inventory.rule"].get_inventory(
            self.property_test.id,
            date_from or self.today,
            date_to or self.today,
            room_type_ids=self.room_type_double.ids,
            **scope,
        )

    def _caps(self, date_from=None, date_to=None, **scope):
        return self.env["pms.inventory.rule"].get_inventory_caps(
            self.property_test.id,
            date_from or self.today,
            date_to or self.today,
            room_type_ids=self.room_type_double.ids,
            **scope,
        )

    def _reservation(self, **values):
        vals = {
            "pms_property_id": self.property_test.id,
            "checkin": self.today,
            "checkout": self.tomorrow,
            "adults": 2,
            "room_type_id": self.room_type_double.id,
            "pricelist_id": self.pricelist_test.id,
            "partner_id": self.guest.id,
        }
        # ``sale_channel_origin_id`` is mandatory on create, and a reservation
        # sold through an agency carries the channel of that agency.
        agency_id = values.get("agency_id")
        if agency_id:
            agency = self.env["res.partner"].browse(agency_id)
            vals["sale_channel_origin_id"] = agency.sale_channel_id.id
        else:
            vals["sale_channel_origin_id"] = self.channel_a.id
        vals.update(values)
        reservation = self.env["pms.reservation"].create(vals)
        reservation.flush_recordset()
        return reservation

    # Resolution against the room type defaults

    def test_no_rule_falls_back_to_room_type_defaults(self):
        """
        With no inventory rule at all, the resolved limits are the room type
        defaults.
        """
        self.room_type_double.write({"default_quota": 4, "default_max_avail": 3})

        inventory = self._inventory()

        self.assertEqual(
            inventory[(self.room_type_double.id, self.today)],
            {"quota": 4, "max_avail": 3},
            "With no rule the room type defaults must be resolved",
        )

    def test_l0_rule_overrides_closing_room_type_default(self):
        """
        A general rule replaces the room type defaults, so an unlimited rule
        opens a room type whose default closes it.

        This is the shape most of the production data has: the room type
        defaults are set to 0 and it is the rules that open the sale.
        """
        self.room_type_double.write({"default_quota": 0, "default_max_avail": 0})
        self._rule(quota=-1, max_avail=-1)

        self.assertEqual(
            self._inventory()[(self.room_type_double.id, self.today)],
            {"quota": -1, "max_avail": -1},
            "A general rule must replace the closing room type defaults",
        )
        self.assertIsNone(
            self._caps()[(self.room_type_double.id, self.today)],
            "An unlimited general rule must leave no cap at all",
        )

    def test_explicit_zero_closes(self):
        """
        A quota of 0 is kept as 0 and closes the scope, instead of being
        replaced by the room type default.
        """
        self.room_type_double.write({"default_quota": 5, "default_max_avail": 5})
        rule = self._rule(quota=0)

        self.assertEqual(rule.quota, 0, "An explicit zero quota must be stored as is")
        self.assertEqual(
            self._caps()[(self.room_type_double.id, self.today)],
            0,
            "A quota of 0 must close the scope",
        )

    # Date ranges

    def test_range_boundaries_are_inclusive(self):
        """
        Both ends of the range are covered by the rule, and the day after is
        not.
        """
        self.room_type_double.write({"default_quota": -1, "default_max_avail": -1})
        day_after = self.today + datetime.timedelta(days=2)
        self._rule(date_from=self.today, date_to=self.tomorrow, quota=2)

        inventory = self._inventory(date_from=self.today, date_to=day_after)

        self.assertEqual(
            inventory[(self.room_type_double.id, self.today)]["quota"],
            2,
            "The first night of the range must be covered",
        )
        self.assertEqual(
            inventory[(self.room_type_double.id, self.tomorrow)]["quota"],
            2,
            "The last night of the range must be covered",
        )
        self.assertEqual(
            inventory[(self.room_type_double.id, day_after)]["quota"],
            -1,
            "The night after the range must fall back to the room type default",
        )

    def test_query_window_narrower_than_rule(self):
        """
        A window narrower than the rule resolves only the nights asked for.
        """
        self._rule(
            date_from=self.today - datetime.timedelta(days=5),
            date_to=self.today + datetime.timedelta(days=5),
            quota=7,
        )

        inventory = self._inventory()

        self.assertEqual(
            list(inventory),
            [(self.room_type_double.id, self.today)],
            "Only the nights of the requested window must be resolved",
        )
        self.assertEqual(inventory[(self.room_type_double.id, self.today)]["quota"], 7)

    def test_same_scope_overlap_last_written_wins(self):
        """
        Two overlapping rules of the same scope: the one written last wins on
        the overlap, and the first one still applies outside it.
        """
        self.room_type_double.write({"default_quota": -1, "default_max_avail": -1})
        last_day = self.today + datetime.timedelta(days=3)
        self._rule(date_from=self.today, date_to=last_day, quota=10)
        self._rule(date_from=self.tomorrow, date_to=self.tomorrow, quota=1)

        inventory = self._inventory(date_from=self.today, date_to=last_day)

        self.assertEqual(
            inventory[(self.room_type_double.id, self.today)]["quota"],
            10,
            "Outside the overlap the wider rule must still apply",
        )
        self.assertEqual(
            inventory[(self.room_type_double.id, self.tomorrow)]["quota"],
            1,
            "On the overlap the rule written last must win",
        )
        self.assertEqual(
            inventory[(self.room_type_double.id, last_day)]["quota"],
            10,
            "After the overlap the wider rule must still apply",
        )

    # Scope levels

    def test_min_across_levels(self):
        """
        The effective limit is the lowest one across the levels that apply,
        whichever level it comes from.
        """
        self.room_type_double.write({"default_quota": -1, "default_max_avail": -1})
        general = self._rule(quota=10)
        channel = self._rule(sale_channel_id=self.channel_a.id, quota=3)

        self.assertEqual(
            self._inventory(sale_channel_id=self.channel_a.id)[
                (self.room_type_double.id, self.today)
            ]["quota"],
            3,
            "The sale channel limit must win when it is the lowest",
        )

        general.quota = 2
        channel.quota = 5

        self.assertEqual(
            self._inventory(sale_channel_id=self.channel_a.id)[
                (self.room_type_double.id, self.today)
            ]["quota"],
            2,
            "The general limit must win when it is the lowest",
        )

    def test_no_limit_is_infinite_across_levels(self):
        """
        A ``-1`` never wins the minimum: it means no limit, not zero.
        """
        self.room_type_double.write({"default_quota": -1, "default_max_avail": -1})
        self._rule(quota=-1)
        self._rule(sale_channel_id=self.channel_a.id, quota=4)

        self.assertEqual(
            self._inventory(sale_channel_id=self.channel_a.id)[
                (self.room_type_double.id, self.today)
            ]["quota"],
            4,
            "An unlimited general rule must not override a channel limit",
        )

    def test_absent_scope_rule_contributes_nothing(self):
        """
        A missing sale channel rule adds nothing to the minimum: the room type
        defaults are the fallback of the general level only.

        Were the defaults folded in for the channel level as well, a room type
        configured with a closing default would close every channel even though
        a general rule opened it.
        """
        self.room_type_double.write({"default_quota": 0, "default_max_avail": 0})
        self._rule(quota=-1, max_avail=-1)

        self.assertIsNone(
            self._caps(sale_channel_id=self.channel_a.id)[
                (self.room_type_double.id, self.today)
            ],
            "A channel without its own rule must not inherit the room type default",
        )

    def test_other_scope_rule_is_ignored(self):
        """
        A rule of another sale channel does not apply.
        """
        self.room_type_double.write({"default_quota": -1, "default_max_avail": -1})
        self._rule(sale_channel_id=self.channel_b.id, quota=1)

        self.assertIsNone(
            self._caps(sale_channel_id=self.channel_a.id)[
                (self.room_type_double.id, self.today)
            ],
            "The rule of another channel must not limit this one",
        )

    def test_zero_closes_only_its_own_scope(self):
        """
        A quota of 0 on a sale channel closes that channel and leaves the
        others open.
        """
        self.room_type_double.write({"default_quota": -1, "default_max_avail": -1})
        self._rule(sale_channel_id=self.channel_a.id, quota=0)

        self.assertEqual(
            self._caps(sale_channel_id=self.channel_a.id)[
                (self.room_type_double.id, self.today)
            ],
            0,
            "The channel with a zero quota must be closed",
        )
        self.assertIsNone(
            self._caps(sale_channel_id=self.channel_b.id)[
                (self.room_type_double.id, self.today)
            ],
            "Another channel must stay open",
        )

    def test_agency_scope_applies(self):
        """
        An agency rule limits that agency only.
        """
        self.room_type_double.write({"default_quota": -1, "default_max_avail": -1})
        self._rule(agency_id=self.agency_a.id, quota=1)

        self.assertEqual(
            self._caps(agency_id=self.agency_a.id)[
                (self.room_type_double.id, self.today)
            ],
            1,
            "The agency rule must limit that agency",
        )
        self.assertIsNone(
            self._caps(agency_id=self.agency_b.id)[
                (self.room_type_double.id, self.today)
            ],
            "Another agency must not be limited",
        )

    # Quota consumption

    def test_quota_consumed_per_night(self):
        """
        A three night stay consumes one room night on each of the three dates,
        not three on the first one.
        """
        self.room_type_double.write({"default_quota": -1, "default_max_avail": -1})
        last_night = self.today + datetime.timedelta(days=2)
        self._rule(date_from=self.today, date_to=last_night, quota=2)
        self._reservation(checkout=self.today + datetime.timedelta(days=3))

        caps = self._caps(date_from=self.today, date_to=last_night)

        for offset in range(3):
            date = self.today + datetime.timedelta(days=offset)
            self.assertEqual(
                caps[(self.room_type_double.id, date)],
                1,
                "Each night of the stay must consume exactly one room night",
            )

    def test_quota_consumption_scoped_by_channel(self):
        """
        A sale through channel A reduces the general quota and the quota of
        channel A, but not the one of channel B.
        """
        self.room_type_double.write({"default_quota": -1, "default_max_avail": -1})
        self._rule(quota=3)
        self._rule(sale_channel_id=self.channel_a.id, quota=3)
        self._rule(sale_channel_id=self.channel_b.id, quota=3)
        self._reservation(sale_channel_origin_id=self.channel_a.id)

        self.assertEqual(
            self._caps(sale_channel_id=self.channel_a.id)[
                (self.room_type_double.id, self.today)
            ],
            2,
            "The quota of the channel that sold must be reduced",
        )
        self.assertEqual(
            self._caps(sale_channel_id=self.channel_b.id)[
                (self.room_type_double.id, self.today)
            ],
            2,
            "The general quota must be reduced for every channel",
        )

        self._rule(sale_channel_id=self.channel_b.id, quota=1)

        self.assertEqual(
            self._caps(sale_channel_id=self.channel_b.id)[
                (self.room_type_double.id, self.today)
            ],
            1,
            "The quota of a channel that sold nothing must be untouched",
        )

    def test_quota_consumption_scoped_by_agency(self):
        """
        A sale through an agency reduces that agency's quota only.
        """
        self.room_type_double.write({"default_quota": -1, "default_max_avail": -1})
        self._rule(agency_id=self.agency_a.id, quota=2)
        self._rule(agency_id=self.agency_b.id, quota=2)
        self._reservation(agency_id=self.agency_a.id)

        self.assertEqual(
            self._caps(agency_id=self.agency_a.id)[
                (self.room_type_double.id, self.today)
            ],
            1,
            "The quota of the agency that sold must be reduced",
        )
        self.assertEqual(
            self._caps(agency_id=self.agency_b.id)[
                (self.room_type_double.id, self.today)
            ],
            2,
            "The quota of another agency must be untouched",
        )

    def test_cancelled_reservation_keeps_the_quota_spent(self):
        """
        Cancelling a reservation does NOT give its quota back.

        A quota of 5 for an agency means "I want to sell 5 through it", and a
        cancelled night was sold all the same. This is also what the counter
        this model replaces did: it fired on the line create without looking
        at any state and never gave anything back.

        Note the contrast with physical availability, which DOES free the
        room: the two measure different things.
        """
        self.room_type_double.write({"default_quota": -1, "default_max_avail": -1})
        self._rule(quota=2)
        reservation = self._reservation()

        self.assertEqual(
            self._caps()[(self.room_type_double.id, self.today)],
            1,
            "A confirmed reservation must consume quota",
        )

        reservation.action_cancel()
        reservation.flush_recordset()

        self.assertEqual(
            self._caps()[(self.room_type_double.id, self.today)],
            1,
            "A cancelled reservation must keep its quota spent",
        )

    def test_max_avail_is_not_consumed(self):
        """
        ``max_avail`` is an exposure cap, not an allowance: a sale does not
        reduce it.

        Reservations already made are reflected in
        ``pms.availability.real_avail``, which the caller intersects with the
        cap, so subtracting them here would count them twice.
        """
        self.room_type_double.write({"default_quota": -1, "default_max_avail": -1})
        self._rule(max_avail=3)
        self._reservation()

        self.assertEqual(
            self._caps()[(self.room_type_double.id, self.today)],
            3,
            "A sale must not reduce the maximum availability",
        )

    def test_upgrade_consumes_the_room_type_sold(self):
        """
        Assigning a room of another room type does not move the consumption:
        the quota spent is the one of the room type sold.
        """
        self.room_type_double.write({"default_quota": -1, "default_max_avail": -1})
        self.room_type_single.write({"default_quota": -1, "default_max_avail": -1})
        self._rule(quota=2)
        single_room = self.room_type_single.room_ids.filtered(
            lambda room: room.pms_property_id == self.property_test
        )
        # One guest only, so that the single room can hold the reservation.
        reservation = self._reservation(adults=1)
        reservation.preferred_room_id = single_room[0]
        reservation.flush_recordset()

        self.assertEqual(
            reservation.room_type_id,
            self.room_type_double,
            "Assigning another room type must not change the room type sold",
        )
        self.assertEqual(
            self._caps()[(self.room_type_double.id, self.today)],
            1,
            "The quota of the room type sold must be the one consumed",
        )

    # Constraints

    def test_scope_exclusivity_constraint(self):
        """
        A rule cannot be limited to a sale channel and to an agency at once.
        """
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self._rule(
                sale_channel_id=self.channel_indirect.id,
                agency_id=self.agency_a.id,
            )

    def test_date_range_constraint(self):
        """
        The last night of a rule cannot be before the first one.
        """
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self._rule(
                date_from=self.tomorrow,
                date_to=self.today,
            )

    def test_no_limit_is_the_lowest_storable_value(self):
        """
        Nothing below ``-1`` can be stored: ``-1`` already means no limit.
        """
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self._rule(quota=-2)

    def test_agency_must_be_an_agency(self):
        """
        The partner of an agency rule has to be an agency.
        """
        with self.assertRaises(ValidationError):
            self._rule(agency_id=self.guest.id)
