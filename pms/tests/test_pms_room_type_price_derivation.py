# Copyright 2026 Commit [Sun]
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
from contextlib import contextmanager
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError, ValidationError

from .common import TestPms


class TestPmsRoomTypePriceDerivation(TestPms):
    """Room types taking their price from another one (their base room type).

    The Double room type is priced in the pricelist and the Superior one is
    set to cost 10 more, with no items of its own.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.date = fields.Date.today() + datetime.timedelta(days=30)
        cls.next_date = cls.date + datetime.timedelta(days=1)
        cls.pms_property2 = cls.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": cls.company1.id,
                "default_pricelist_id": cls.pricelist1.id,
            }
        )
        cls.pricelist2 = cls.env["product.pricelist"].create(
            {
                "name": "Pricelist 2",
                "availability_plan_id": cls.availability_plan1.id,
                "is_pms_available": True,
            }
        )
        cls.double = cls._create_room_type("Double", "PD_DBL", list_price=400.0)
        cls.superior = cls._create_room_type(
            "Superior",
            "PD_SUP",
            list_price=300.0,
            price_base_room_type_id=cls.double.id,
            price_derivation_value=10.0,
        )
        cls.double_item = cls._set_price(cls.double, cls.date, 100.0)
        cls._set_price(cls.double, cls.next_date, 120.0)

    @classmethod
    def _create_room_type(cls, name, code, **vals):
        values = {
            "name": name,
            "default_code": code,
            "class_id": cls.room_type_class1.id,
            "pms_property_ids": [(6, 0, [cls.pms_property1.id])],
        }
        values.update(vals)
        return cls.env["pms.room.type"].create(values)

    @classmethod
    def _set_price(cls, room_type, date, price, pricelist=None, pms_property=None):
        return cls.env["product.pricelist.item"].create(
            {
                "pricelist_id": (pricelist or cls.pricelist1).id,
                "applied_on": "0_product_variant",
                "product_id": room_type.product_id.id,
                "compute_price": "fixed",
                "fixed_price": price,
                "date_start_consumption": date,
                "date_end_consumption": date,
                "pms_property_ids": [(6, 0, (pms_property or cls.pms_property1).ids)],
            }
        )

    @contextmanager
    def _assert_refused(self, exception, message):
        """assertRaisesRegex rolling back what the refused operation wrote."""
        with self.assertRaises(exception) as refusal:
            yield
        self.assertIn(message, str(refusal.exception))

    def _price(self, room_type, date=None, pricelist=None, pms_property=None, **kw):
        return (pricelist or self.pricelist1)._get_product_price(
            product=room_type.product_id,
            quantity=1,
            consumption_date=date or self.date,
            pms_property_id=(pms_property or self.pms_property1).id,
            **kw,
        )

    # Price computation

    def test_amount_variation(self):
        """The variation is added to the price of the base room type."""
        self.assertAlmostEqual(self._price(self.superior), 110.0, places=2)
        self.assertAlmostEqual(
            self._price(self.superior, self.next_date), 130.0, places=2
        )
        self.superior.price_derivation_value = -15.0
        self.assertAlmostEqual(
            self._price(self.superior),
            85.0,
            places=2,
            msg="A change of the variation applies right away",
        )

    def test_percent_variation_rounded_to_currency(self):
        """With no rounding set, a percentage is rounded to the currency."""
        self._set_price(self.double, self.date + datetime.timedelta(days=2), 65.57)
        self.superior.write(
            {"price_derivation_type": "percent", "price_derivation_value": 10.0}
        )
        self.assertAlmostEqual(self._price(self.superior), 110.0, places=2)
        self.assertAlmostEqual(
            self._price(self.superior, self.date + datetime.timedelta(days=2)),
            72.13,
            places=2,
            msg="65.57 + 10% = 72.127 rounds to the cent",
        )

    def test_percent_variation_rounded_to_multiple(self):
        """A percentage is rounded to the multiple set on the room type."""
        self._set_price(self.double, self.date + datetime.timedelta(days=2), 65.0)
        self.superior.write(
            {
                "price_derivation_type": "percent",
                "price_derivation_value": 10.0,
                "price_derivation_rounding": 1.0,
            }
        )
        self.assertAlmostEqual(
            self._price(self.superior, self.date + datetime.timedelta(days=2)),
            72.0,
            places=2,
            msg="65 + 10% = 71.5 rounds to 72",
        )
        self.superior.price_derivation_rounding = 5.0
        self.assertAlmostEqual(
            self._price(self.superior, self.date + datetime.timedelta(days=2)),
            70.0,
            places=2,
        )

    def test_own_item_overrides_its_date_only(self):
        """An item of the derived room type sets its price on its date."""
        self._set_price(self.superior, self.date, 150.0)
        self.assertAlmostEqual(self._price(self.superior), 150.0, places=2)
        self.assertAlmostEqual(
            self._price(self.superior, self.next_date),
            130.0,
            places=2,
            msg="The other dates keep following the base room type",
        )

    def test_chain_of_derivations(self):
        """A base room type can derive its price from a third one."""
        family = self._create_room_type(
            "Family",
            "PD_FAM",
            price_base_room_type_id=self.superior.id,
            price_derivation_type="percent",
            price_derivation_value=5.0,
        )
        self.assertAlmostEqual(
            self._price(family), 115.5, places=2, msg="(100 + 10) + 5%"
        )
        self.assertEqual(
            self.double._get_price_derivation_descendants(),
            self.superior | family,
        )
        self.assertEqual(
            self.double._get_price_derivation_descendants()[0],
            self.superior,
            "Each room type comes after the one its price derives from",
        )

    def test_base_without_rule_uses_its_list_price(self):
        """With no rule for the base room type, its list price is the base."""
        date = self.date + datetime.timedelta(days=5)
        self.assertAlmostEqual(self._price(self.double, date), 400.0, places=2)
        self.assertAlmostEqual(self._price(self.superior, date), 410.0, places=2)

    def test_price_never_goes_negative(self):
        """A negative variation larger than the base price floors at zero."""
        self.superior.price_derivation_value = -150.0
        self.assertEqual(self._price(self.superior), 0.0)

    def test_price_per_property(self):
        """The base price is the one of the property being priced."""
        properties = self.pms_property1 | self.pms_property2
        twin = self._create_room_type(
            "Twin", "PD_TWN", pms_property_ids=[(6, 0, properties.ids)]
        )
        twin_superior = self._create_room_type(
            "Twin Superior",
            "PD_TWS",
            pms_property_ids=[(6, 0, properties.ids)],
            price_base_room_type_id=twin.id,
            price_derivation_value=10.0,
        )
        self._set_price(twin, self.date, 100.0)
        self._set_price(twin, self.date, 200.0, pms_property=self.pms_property2)
        self.assertAlmostEqual(self._price(twin_superior), 110.0, places=2)
        self.assertAlmostEqual(
            self._price(twin_superior, pms_property=self.pms_property2),
            210.0,
            places=2,
        )

    def test_generic_rule_wins_over_derivation(self):
        """A category or global rule covering the room type is a rule of its own.

        The derivation only applies when the pricelist has no rule at all for
        the room type, so a generic rule of the pricelist prices it instead.
        """
        self.env["product.pricelist.item"].create(
            {
                "pricelist_id": self.pricelist1.id,
                "applied_on": "2_product_category",
                "categ_id": self.superior.categ_id.id,
                "compute_price": "percentage",
                "percent_price": 50.0,
            }
        )
        self.assertAlmostEqual(
            self._price(self.superior), 150.0, places=2, msg="50% of 300"
        )
        self.assertAlmostEqual(
            self._price(self.double),
            100.0,
            places=2,
            msg="Items of the room type itself still win over the generic rule",
        )

    def test_pricelist_restriction(self):
        """The price is only derived in the pricelists set on the room type."""
        self._set_price(self.double, self.date, 90.0, pricelist=self.pricelist2)
        self.superior.price_derivation_pricelist_ids = self.pricelist1
        self.assertAlmostEqual(self._price(self.superior), 110.0, places=2)
        self.assertAlmostEqual(
            self._price(self.superior, pricelist=self.pricelist2),
            300.0,
            places=2,
            msg="Out of its pricelists, the room type gets its own list price",
        )
        self.assertFalse(self.superior._get_price_derivation(self.pricelist2))
        self.assertEqual(
            self.superior._get_price_derivation(self.pricelist1), self.superior
        )
        self.assertFalse(self.superior._get_price_derivation(self.pricelist1.browse()))

    def test_pricelist_restriction_to_archived_pricelist(self):
        """Archiving the pricelists the price is derived in never widens it."""
        old_rate = self.env["product.pricelist"].create(
            {"name": "Old Rate", "availability_plan_id": self.availability_plan1.id}
        )
        self.superior.price_derivation_pricelist_ids = old_rate
        old_rate.active = False
        self.assertFalse(self.superior._get_price_derivation(self.pricelist1))
        self.assertAlmostEqual(self._price(self.superior), 300.0, places=2)

    def test_derived_pricelist_with_generic_rule_on_top(self):
        """A pricelist based on another one by a generic rule applies on top.

        E.g. a channel rate being 38% more than the standard one: the derived
        room type gets 38% more than its derived standard price.
        """
        channel_pricelist = self.env["product.pricelist"].create(
            {
                "name": "Channel",
                "item_ids": [
                    (
                        0,
                        0,
                        {
                            "applied_on": "2_product_category",
                            "categ_id": self.superior.categ_id.id,
                            "compute_price": "formula",
                            "base": "pricelist",
                            "base_pricelist_id": self.pricelist1.id,
                            "price_discount": -38.0,
                        },
                    )
                ],
            }
        )
        self.assertAlmostEqual(
            self._price(self.double, pricelist=channel_pricelist), 138.0, places=2
        )
        self.assertAlmostEqual(
            self._price(self.superior, pricelist=channel_pricelist),
            151.8,
            places=2,
            msg="(100 + 10) * 1.38",
        )

    def test_derived_pricelist_with_rules_for_base_only(self):
        """A pricelist with rules on the base room type only derives from them.

        When a pricelist based on another one holds product rules for the base
        room type and none for the derived one, the derived room type has no
        rule there: its price is derived in that pricelist, from the price of
        the base room type in it (its surcharge included), and not computed by
        those rules on top of its own base price.
        """
        breakfast_pricelist = self.env["product.pricelist"].create(
            {
                "name": "Bed and breakfast",
                "item_ids": [
                    (
                        0,
                        0,
                        {
                            "applied_on": "0_product_variant",
                            "product_id": self.double.product_id.id,
                            "compute_price": "formula",
                            "base": "pricelist",
                            "base_pricelist_id": self.pricelist1.id,
                            "price_surcharge": 16.0,
                        },
                    )
                ],
            }
        )
        self.superior.write(
            {"price_derivation_type": "percent", "price_derivation_value": 10.0}
        )
        self.assertAlmostEqual(
            self._price(self.double, pricelist=breakfast_pricelist), 116.0, places=2
        )
        self.assertAlmostEqual(
            self._price(self.superior, pricelist=breakfast_pricelist),
            127.6,
            places=2,
            msg="(100 + 16) + 10%, not (100 + 10%) + 16",
        )
        self.superior.price_derivation_pricelist_ids = self.pricelist1
        self.assertAlmostEqual(
            self._price(self.superior, pricelist=breakfast_pricelist),
            300.0,
            places=2,
            msg="Not derived there, the room type falls back to its list price",
        )

    def test_base_price_ignores_guest_details(self):
        """Only the stay is forwarded to price the base room type.

        Whatever depends on the guests (e.g. the occupancy) is for the derived
        room type to apply on its own price, never through its base as well.
        """
        pricelist_class = type(self.env["product.pricelist"])
        get_product_price = pricelist_class._get_product_price
        calls = []

        def spy(pricelist, product, *args, **kwargs):
            calls.append((product, kwargs))
            return get_product_price(pricelist, product, *args, **kwargs)

        with patch.object(pricelist_class, "_get_product_price", spy):
            price = self._price(self.superior, occupancy=3, children=1)
        self.assertAlmostEqual(price, 110.0, places=2)
        base_calls = [kw for product, kw in calls if product == self.double.product_id]
        self.assertEqual(len(base_calls), 1)
        self.assertEqual(
            set(base_calls[0]),
            {
                "uom",
                "date",
                "consumption_date",
                "pms_property_id",
                "price_derivation_depth",
            },
        )

    def test_no_pricelist_keeps_list_price(self):
        """Without a pricelist to derive in, the price is the list price."""
        price = self.env["product.pricelist.item"]._compute_consumption_price(
            self.superior.product_id,
            1,
            self.superior.uom_id,
            fields.Datetime.now(),
            currency=self.pricelist1.currency_id,
            consumption_date=self.date,
            pms_property_id=self.pms_property1.id,
        )
        self.assertAlmostEqual(price, 300.0, places=2)

    def test_other_products_unaffected(self):
        """Products other than derived room types keep their list price."""
        product = self.env["product.product"].create(
            {"name": "Extra Bed", "list_price": 7.0}
        )
        self.assertAlmostEqual(
            self.pricelist1._get_product_price(
                product,
                1,
                consumption_date=self.date,
                pms_property_id=self.pms_property1.id,
            ),
            7.0,
            places=2,
        )
        date = self.date + datetime.timedelta(days=5)
        self.assertAlmostEqual(self._price(self.double, date), 400.0, places=2)

    # Configuration

    def test_derivation_loop_rejected(self):
        """A room type cannot derive its price through itself."""
        with self._assert_refused(ValidationError, "from itself"):
            self.double.price_base_room_type_id = self.superior
        with self._assert_refused(ValidationError, "from itself"):
            self.double.price_base_room_type_id = self.double

    def test_too_many_levels_rejected(self):
        """Chains are limited to the levels the engine follows."""
        room_type = self.double
        for level in range(1, 10):
            room_type = self._create_room_type(
                f"Level {level}",
                f"PD_LVL{level}",
                price_base_room_type_id=room_type.id,
                price_derivation_value=1.0,
            )
        self.assertEqual(room_type._get_price_derivation_depth(), 9)
        self.assertAlmostEqual(self._price(room_type), 109.0, places=2)
        room_type = self._create_room_type(
            "Level 10",
            "PD_LVL10",
            price_base_room_type_id=room_type.id,
            price_derivation_value=1.0,
        )
        self.assertAlmostEqual(self._price(room_type), 110.0, places=2)
        with self._assert_refused(ValidationError, "too many levels"):
            self._create_room_type(
                "Level 11", "PD_LVL11", price_base_room_type_id=room_type.id
            )
        with self._assert_refused(ValidationError, "too many levels"):
            self.double.price_base_room_type_id = self._create_room_type(
                "Root", "PD_ROOT"
            )

    def test_runtime_depth_guard(self):
        """The engine refuses to go deeper than the levels it follows."""
        with self._assert_refused(UserError, "too many levels"):
            self._price(self.superior, price_derivation_depth=10)

    def test_percentage_down_to_minus_100_rejected(self):
        """A percentage cannot take the price down to zero or below."""
        with self._assert_refused(ValidationError, "greater than -100%"):
            self.superior.write(
                {"price_derivation_type": "percent", "price_derivation_value": -100}
            )
        self.superior.write(
            {"price_derivation_type": "percent", "price_derivation_value": -50}
        )
        self.assertAlmostEqual(self._price(self.superior), 50.0, places=2)
        self.superior.price_derivation_type = "amount"
        self.superior.price_derivation_value = -100
        self.assertAlmostEqual(
            self._price(self.superior),
            0.0,
            places=2,
            msg="Amounts are not limited, the price floors at zero",
        )

    def test_negative_rounding_rejected(self):
        with self._assert_refused(ValidationError, "rounding"):
            self.superior.price_derivation_rounding = -1.0

    def test_base_in_other_property_rejected(self):
        """The base room type must be available in all the properties."""
        other = self._create_room_type(
            "Other", "PD_OTH", pms_property_ids=[(6, 0, self.pms_property2.ids)]
        )
        with self.assertRaises(UserError):
            self.superior.price_base_room_type_id = other

    # Flows

    def test_reservation_derived_price_and_update_prices(self):
        """Reservations get the derived price and keep it until recomputed."""
        self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Superior 101",
                "room_type_id": self.superior.id,
                "capacity": 2,
            }
        )
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": self.date,
                "checkout": self.date + datetime.timedelta(days=2),
                "room_type_id": self.superior.id,
                "partner_id": self.env["res.partner"].create({"name": "Guest"}).id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "sale_channel_origin_id": self.env["pms.sale.channel"]
                .create({"name": "Door", "channel_type": "direct"})
                .id,
            }
        )
        lines = reservation.reservation_line_ids.sorted("date")
        self.assertEqual(lines.mapped("price"), [110.0, 130.0])
        self.double_item.fixed_price = 200.0
        self.assertEqual(
            lines.mapped("price"),
            [110.0, 130.0],
            "Prices set on reservations do not follow later changes",
        )
        reservation.update_prices()
        self.assertEqual(lines.mapped("price"), [210.0, 130.0])

    def test_booking_engine_price(self):
        """The booking engine prices the stay with the derived prices."""
        total = self.env["pms.folio.availability.wizard"]._get_price_by_room_type(
            room_type_id=self.superior.id,
            checkin=self.date,
            checkout=self.date + datetime.timedelta(days=2),
            board_service_room_id=False,
            pricelist_id=self.pricelist1.id,
            pms_property_id=self.pms_property1.id,
        )
        self.assertAlmostEqual(total, 240.0, places=2)

    # Massive changes wizard

    def _massive_changes(self, pricelists, room_types=None, price=50.0):
        vals = {
            "massive_changes_on": "pricelist",
            "pricelist_ids": [(6, 0, pricelists.ids)],
            "start_date": self.date,
            "end_date": self.date,
            "pms_property_ids": [(6, 0, self.pms_property1.ids)],
            "price": price,
        }
        if room_types:
            vals["room_type_ids"] = [(6, 0, room_types.ids)]
        return self.env["pms.massive.changes.wizard"].create(vals)

    def _items(self, room_type, pricelist):
        return self.env["product.pricelist.item"].search(
            [
                ("pricelist_id", "=", pricelist.id),
                ("product_id", "=", room_type.product_id.id),
                ("date_start_consumption", "=", self.date),
            ]
        )

    def test_massive_changes_leave_derived_room_types_out(self):
        """With no room type selected, derived room types keep following."""
        self.superior.price_derivation_pricelist_ids = self.pricelist1
        wizard = self._massive_changes(self.pricelist1 | self.pricelist2)
        self.assertEqual(wizard.price_derived_room_type_ids, self.superior)
        wizard.apply_massive_changes()
        self.assertFalse(self._items(self.superior, self.pricelist1))
        self.assertAlmostEqual(self._price(self.superior), 60.0, places=2)
        self.assertTrue(
            self._items(self.superior, self.pricelist2),
            "Where it is not derived, the room type gets the price as usual",
        )
        self.assertAlmostEqual(
            self._price(self.superior, pricelist=self.pricelist2), 50.0, places=2
        )

    def test_massive_changes_keep_overrides(self):
        """Overrides of derived room types are neither replaced nor removed."""
        override = self._set_price(self.superior, self.date, 150.0)
        wizard = self._massive_changes(self.pricelist1)
        self.assertNotIn(override, wizard.pricelist_items_to_overwrite)
        self.assertIn(self.double_item, wizard.pricelist_items_to_overwrite)
        wizard.apply_massive_changes()
        self.assertTrue(override.exists())
        self.assertAlmostEqual(self._price(self.superior), 150.0, places=2)
        self.assertAlmostEqual(self._price(self.double), 50.0, places=2)

    def test_massive_changes_selected_derived_room_type_gets_price(self):
        """Selecting a derived room type sets a price of its own (override)."""
        wizard = self._massive_changes(self.pricelist1, room_types=self.superior)
        self.assertFalse(wizard.price_derived_room_type_ids)
        wizard.apply_massive_changes()
        self.assertAlmostEqual(self._price(self.superior), 50.0, places=2)
        self.assertAlmostEqual(self._price(self.double), 100.0, places=2)

    def test_massive_changes_on_availability_unchanged(self):
        """Availability changes still apply to every room type."""
        availability_plan = self.env["pms.availability.plan"].create(
            {"name": "Availability plan", "pms_pricelist_ids": [self.pricelist1.id]}
        )
        wizard = self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "availability_plan",
                "availability_plan_ids": [(6, 0, availability_plan.ids)],
                "start_date": self.date,
                "end_date": self.date,
                "pms_property_ids": [(6, 0, self.pms_property1.ids)],
                "apply_closed": True,
                "closed": True,
            }
        )
        self.assertFalse(wizard.price_derived_room_type_ids)
        wizard.apply_massive_changes()
        self.assertIn(self.superior, availability_plan.rule_ids.room_type_id)

    # Users with access to some properties only

    def _user_env(self, login, pms_property, groups):
        """The environment of a request of a user of the property only.

        Its cache starts empty, as in a request: values read before by the
        superuser would hide what the user can read.
        """
        user = self.env["res.users"].create(
            {
                "name": login,
                "login": login,
                "company_id": self.company1.id,
                "company_ids": [(6, 0, self.company1.ids)],
                "pms_property_ids": [(6, 0, pms_property.ids)],
                "pms_property_id": pms_property.id,
                "groups_id": [(6, 0, [self.env.ref(group).id for group in groups])],
            }
        )
        self.env.invalidate_all()
        return self.env(
            user=user,
            context=dict(self.env.context, allowed_company_ids=self.company1.ids),
        )

    def _derivation_restricted_to_property1(self):
        """Room types of all the properties deriving in a rate of property 1.

        The base room type is priced in a rate of property 2, where the derived
        one does not derive. Users of property 2 cannot read the rate of
        property 1 the derivation is restricted to.
        """
        rate_property1, rate_property2 = self.env["product.pricelist"].create(
            [
                {
                    "name": f"Rate of {pms_property.name}",
                    "pms_property_ids": [(6, 0, pms_property.ids)],
                    "availability_plan_id": self.availability_plan1.id,
                }
                for pms_property in self.pms_property1 | self.pms_property2
            ]
        )
        double = self._create_room_type(
            "Shared Double",
            "PD_SHDBL",
            list_price=400.0,
            pms_property_ids=[(6, 0, [])],
        )
        superior = self._create_room_type(
            "Shared Superior",
            "PD_SHSUP",
            list_price=300.0,
            pms_property_ids=[(6, 0, [])],
            price_base_room_type_id=double.id,
            price_derivation_value=10.0,
            price_derivation_pricelist_ids=[(6, 0, rate_property1.ids)],
        )
        self._set_price(
            double,
            self.date,
            100.0,
            pricelist=rate_property2,
            pms_property=self.pms_property2,
        )
        return rate_property2, superior

    def test_restriction_does_not_depend_on_user_access(self):
        """A restriction to rates the user cannot read is still a restriction.

        Read with the access of the user, it would be empty, i.e. all the
        pricelists, and the price would depend on who computes it.
        """
        rate, superior = self._derivation_restricted_to_property1()
        self.assertAlmostEqual(
            self._price(superior, pricelist=rate, pms_property=self.pms_property2),
            300.0,
            places=2,
            msg="Not derived in the rate, the room type gets its list price",
        )
        env = self._user_env(
            "pd_front_desk",
            self.pms_property2,
            ["base.group_user", "pms.group_pms_user"],
        )
        self.assertAlmostEqual(
            self._price(
                superior.with_env(env),
                pricelist=rate.with_env(env),
                pms_property=self.pms_property2,
            ),
            300.0,
            places=2,
        )
        env.invalidate_all()
        self.assertFalse(superior.with_env(env)._get_price_derivation(rate))

    def test_massive_changes_do_not_depend_on_user_access(self):
        """Users leave the same room types out whatever rates they can read."""
        rate, superior = self._derivation_restricted_to_property1()
        env = self._user_env(
            "pd_revenue_manager",
            self.pms_property2,
            [
                "base.group_user",
                "pms.group_pms_manager",
                "sales_team.group_sale_manager",
            ],
        )
        wizard = env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "pricelist",
                "pricelist_ids": [(6, 0, rate.ids)],
                "start_date": self.date,
                "end_date": self.date,
                "pms_property_ids": [(6, 0, self.pms_property2.ids)],
                "price": 50.0,
            }
        )
        self.assertFalse(wizard.price_derived_room_type_ids)
        wizard.apply_massive_changes()
        self.assertAlmostEqual(
            self._price(superior, pricelist=rate, pms_property=self.pms_property2),
            50.0,
            places=2,
            msg="Not derived in the rate, the room type gets the price as usual",
        )

    def test_too_many_levels_beyond_user_access(self):
        """Room types the user cannot read count for the levels as well."""
        root = room_type = self._create_room_type(
            "Shared Level 0", "PD_SHL0", pms_property_ids=[(6, 0, [])]
        )
        for level in range(1, 10):
            room_type = self._create_room_type(
                f"Shared Level {level}",
                f"PD_SHL{level}",
                pms_property_ids=[(6, 0, [])],
                price_base_room_type_id=room_type.id,
            )
        # Of property 1, out of the access of the users of property 2
        self._create_room_type(
            "Level 10", "PD_SHL10", price_base_room_type_id=room_type.id
        )
        new_root = self._create_room_type(
            "Shared Root", "PD_SHROOT", pms_property_ids=[(6, 0, [])]
        )
        env = self._user_env(
            "pd_manager",
            self.pms_property2,
            ["base.group_user", "pms.group_pms_manager"],
        )
        with self._assert_refused(ValidationError, "too many levels"):
            root.with_env(env).price_base_room_type_id = new_root

    # Translations

    def test_spanish_translations(self):
        """The new labels and messages are translated into Spanish."""
        self.env["res.lang"]._activate_lang("es_ES")
        self.env.ref("base.module_pms")._update_translations(["es_ES"])
        env_es = self.env(context=dict(self.env.context, lang="es_ES"))
        self.assertEqual(
            env_es["ir.model.fields"]
            ._get("pms.room.type", "price_base_room_type_id")
            .field_description,
            "Precio derivado de",
        )
        left_out = env_es["ir.model.fields"]._get(
            "pms.massive.changes.wizard", "price_derived_room_type_ids"
        )
        self.assertEqual(left_out.field_description, "Excluidos (precio derivado)")
        self.assertIn("precio propio, que se mantiene", left_out.help)
        self.assertIn("Selecciónelos expresamente", left_out.help)
        self.assertIn(
            "Déjelo vacío",
            env_es["ir.model.fields"]
            ._get("pms.room.type", "price_derivation_pricelist_ids")
            .help,
        )
        arch = env_es["pms.room.type"].get_view(
            self.env.ref("pms.pms_room_type_view_form").id, "form"
        )["arch"]
        self.assertIn("Precio derivado", arch)
        with self._assert_refused(ValidationError, "sí mismo"):
            self.double.with_env(env_es).price_base_room_type_id = self.superior
        with self._assert_refused(UserError, "demasiados niveles"):
            self._price(
                self.superior.with_env(env_es),
                pricelist=self.pricelist1.with_env(env_es),
                price_derivation_depth=10,
            )
