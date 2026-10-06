import datetime

from odoo.exceptions import ValidationError

from .common import TestPms


class TestPmsPricelistOccupancy(TestPms):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.consumption_date = datetime.date(2012, 1, 14)
        cls.room_type = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Quadruple",
                "default_code": "QDR",
                "class_id": cls.room_type_class1.id,
            }
        )
        for number in range(1, 3):
            cls.env["pms.room"].create(
                {
                    "pms_property_id": cls.pms_property1.id,
                    "name": "Quadruple-%s" % number,
                    "room_type_id": cls.room_type.id,
                    "capacity": 4,
                }
            )
        cls.env["product.pricelist.item"].create(
            {
                "pricelist_id": cls.pricelist1.id,
                "applied_on": "0_product_variant",
                "product_id": cls.room_type.product_id.id,
                "compute_price": "fixed",
                "fixed_price": 100.0,
                "date_start_consumption": cls.consumption_date,
                "date_end_consumption": cls.consumption_date,
                "pms_property_ids": [(6, 0, [cls.pms_property1.id])],
            }
        )

    def _price(self, occupancy):
        return self.pricelist1._get_product_price(
            product=self.room_type.product_id,
            quantity=1,
            consumption_date=self.consumption_date,
            pms_property_id=self.pms_property1.id,
            occupancy=occupancy,
        )

    def _set_modifiers(self, **values):
        return self.env["pms.pricelist.occupancy"].create(
            dict(
                values,
                pricelist_id=self.pricelist1.id,
                room_type_id=self.room_type.id,
            )
        )

    def test_default_occupancy_defaults_to_max(self):
        """The room type is priced for the occupancy its rooms guarantee."""
        self.assertEqual(self.room_type.max_occupancy, 4)
        self.assertEqual(self.room_type.default_occupancy, 4)

    def test_price_without_modifiers_is_the_pricelist_one(self):
        """A pricelist with no modifiers prices the room type as before."""
        self.assertAlmostEqual(self._price(1), 100.0, places=2)
        self.assertAlmostEqual(self._price(4), 100.0, places=2)

    def test_price_without_occupancy_is_the_pricelist_one(self):
        """Callers that do not ask for an occupancy get the plain price."""
        self._set_modifiers(decrease_mode="percent", decrease_value=25.0)
        self.assertAlmostEqual(
            self.pricelist1._get_product_price(
                product=self.room_type.product_id,
                quantity=1,
                consumption_date=self.consumption_date,
                pms_property_id=self.pms_property1.id,
            ),
            100.0,
            places=2,
        )

    def test_decrease_below_default_occupancy(self):
        """Each guest below the default occupancy discounts the price."""
        self._set_modifiers(decrease_mode="percent", decrease_value=25.0)
        self.assertAlmostEqual(self._price(4), 100.0, places=2)
        self.assertAlmostEqual(self._price(3), 75.0, places=2)
        self.assertAlmostEqual(self._price(2), 50.0, places=2)

    def test_increase_above_default_occupancy(self):
        """Each guest above the default occupancy charges more."""
        self.room_type.default_occupancy = 2
        self._set_modifiers(increase_mode="percent", increase_value=5.0)
        self.assertAlmostEqual(self._price(2), 100.0, places=2)
        self.assertAlmostEqual(self._price(3), 105.0, places=2)

    def test_modifier_is_linear_not_compound(self):
        """Two guests of difference charge twice, they do not compound."""
        self.room_type.default_occupancy = 2
        self._set_modifiers(increase_mode="percent", increase_value=5.0)
        self.assertAlmostEqual(
            self._price(4),
            110.0,
            places=2,
            msg="A 5% increase for two guests is 10%, not 5% twice (110.25)",
        )

    def test_fixed_amount_modifier(self):
        """The modifier can be an amount instead of a percentage."""
        self._set_modifiers(decrease_mode="amount", decrease_value=12.0)
        self.assertAlmostEqual(self._price(3), 88.0, places=2)
        self.assertAlmostEqual(self._price(2), 76.0, places=2)

    def test_price_never_goes_negative(self):
        """A decrease larger than the price itself floors at zero."""
        self._set_modifiers(decrease_mode="amount", decrease_value=80.0)
        self.assertAlmostEqual(self._price(1), 0.0, places=2)

    def test_no_modifiers_set_keeps_price(self):
        """A configuration with no values set leaves the price alone."""
        self._set_modifiers()
        self.assertAlmostEqual(self._price(1), 100.0, places=2)

    def test_zero_default_occupancy_prices_regardless_of_guests(self):
        """A room type with no default occupancy is priced as a flat rate."""
        self.room_type.default_occupancy = 0
        self._set_modifiers(decrease_mode="percent", decrease_value=25.0)
        self.assertAlmostEqual(self._price(1), 100.0, places=2)

    def test_default_occupancy_above_max_is_rejected(self):
        """A room type cannot be priced for more guests than it guarantees."""
        with self.assertRaisesRegex(ValidationError, "guarantees"):
            self.room_type.default_occupancy = 5

    def test_room_type_without_rooms_accepts_any_default_occupancy(self):
        """A room type is created before its rooms, so it is left alone."""
        room_type = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Not built yet",
                "default_code": "NBY",
                "class_id": self.room_type_class1.id,
                "default_occupancy": 3,
            }
        )
        self.assertEqual(room_type.max_occupancy, 0)
        self.assertEqual(room_type.default_occupancy, 3)

    def test_negative_modifier_is_rejected(self):
        """The direction comes from the field, so values are amounts."""
        with self.assertRaisesRegex(ValidationError, "negative"):
            self._set_modifiers(decrease_mode="percent", decrease_value=-25.0)
