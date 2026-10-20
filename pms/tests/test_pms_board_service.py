# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime

from odoo import fields
from odoo.exceptions import UserError, ValidationError

from .common import TestPms


class TestBoardService(TestPms):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.room_type = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Triple",
                "default_code": "TRP",
                "class_id": cls.room_type_class1.id,
            }
        )
        cls.room = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Triple 101",
                "room_type_id": cls.room_type.id,
                "capacity": 3,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Guest"})
        cls.sale_channel = cls.env["pms.sale.channel"].create(
            {"name": "Door", "channel_type": "direct"}
        )
        # Breakfast with its own price for children
        cls.breakfast = cls._create_board_service(
            "Breakfast",
            guests=("adult", "child"),
            list_price=10,
            per_day=True,
            per_person=True,
        )
        cls.adult_breakfast = cls._board_service_variant(cls.breakfast, "adults")
        cls.child_breakfast = cls._board_service_variant(cls.breakfast, "children")
        cls.pricelist1.write(
            {"is_pms_available": True, "board_service_ids": [(4, cls.breakfast.id)]}
        )
        cls.checkin = fields.date.today() + datetime.timedelta(days=10)
        cls.checkout = cls.checkin + datetime.timedelta(days=2)

    def _create_reservation(self, **vals):
        return self.env["pms.reservation"].create(
            dict(
                {
                    "checkin": self.checkin,
                    "checkout": self.checkout,
                    "room_type_id": self.room_type.id,
                    "pms_property_id": self.pms_property1.id,
                    "partner_id": self.partner.id,
                    "pricelist_id": self.pricelist1.id,
                    "sale_channel_origin_id": self.sale_channel.id,
                    "adults": 2,
                },
                **vals,
            )
        )

    def _board_services(self, reservation):
        return {
            (service.product_id, service.board_guest_type): set(
                service.service_line_ids.mapped("day_qty")
            )
            for service in reservation.service_ids.filtered("is_board_service")
        }

    # CONSUMPTION
    def test_each_guest_consumes_its_variant(self):
        """
        Adults and children consume the variant of the board service for
        them, each one counted by its own guests.
        """
        # ACT
        reservation = self._create_reservation(
            adults=2, children=1, board_service_id=self.breakfast.id
        )
        # ASSERT
        self.assertEqual(
            self._board_services(reservation),
            {
                (self.adult_breakfast, "adults"): {2},
                (self.child_breakfast, "children"): {1},
            },
        )

    def test_board_service_without_guest_attribute_for_every_guest(self):
        """
        A board service without the Guest attribute is a single product that
        counts adults and children.
        """
        # ARRANGE
        breakfast = self._create_board_service(
            "Breakfast for all", guests=(), per_day=True, per_person=True
        )
        # ACT
        reservation = self._create_reservation(
            adults=2, children=1, board_service_id=breakfast.id
        )
        # ASSERT
        self.assertEqual(
            self._board_services(reservation),
            {(breakfast.product_variant_id, "all"): {3}},
        )

    def test_adults_only_board_service_leaves_children_out(self):
        """
        A board service only with the Adult value isn't consumed by children.
        """
        # ARRANGE
        half_board = self._create_board_service(
            "Half Board", guests=("adult",), per_day=True, per_person=True
        )
        # ACT
        reservation = self._create_reservation(
            adults=2, children=1, board_service_id=half_board.id
        )
        # ASSERT
        self.assertEqual(
            self._board_services(reservation),
            {(half_board.product_variant_id, "adults"): {2}},
        )

    def test_children_variant_follows_the_children_of_the_reservation(self):
        """
        Adding children adds the variant for them without touching the adults
        one, and removing them removes it.
        """
        # ARRANGE
        reservation = self._create_reservation(
            adults=2, board_service_id=self.breakfast.id
        )
        adult_service = reservation.service_ids.filtered("is_board_service")
        # ACT & ASSERT
        reservation.children = 1
        self.assertEqual(
            self._board_services(reservation),
            {
                (self.adult_breakfast, "adults"): {2},
                (self.child_breakfast, "children"): {1},
            },
        )
        self.assertIn(adult_service, reservation.service_ids)
        reservation.children = 0
        self.assertEqual(
            self._board_services(reservation),
            {(self.adult_breakfast, "adults"): {2}},
        )
        self.assertIn(adult_service, reservation.service_ids)

    def test_room_only_never_consumes_anything(self):
        """
        Room Only exists to sell rooms without board service: it never adds a
        service to a reservation.
        """
        # ACT
        reservation = self._create_reservation(
            board_service_id=self.board_service_room_only.id
        )
        # ASSERT
        self.assertFalse(reservation.service_ids.filtered("is_board_service"))

    # PRICES
    def test_variants_priced_by_the_pricelist(self):
        """
        Each variant of a board service takes the price of the pricelist.
        """
        # ARRANGE
        for product, price in ((self.adult_breakfast, 12), (self.child_breakfast, 6)):
            self.env["product.pricelist.item"].create(
                {
                    "pricelist_id": self.pricelist1.id,
                    "applied_on": "0_product_variant",
                    "product_id": product.id,
                    "compute_price": "fixed",
                    "fixed_price": price,
                }
            )
        # ACT
        reservation = self._create_reservation(
            adults=2, children=1, board_service_id=self.breakfast.id
        )
        # ASSERT
        prices = {
            service.product_id: set(service.service_line_ids.mapped("price_unit"))
            for service in reservation.service_ids.filtered("is_board_service")
        }
        self.assertEqual(
            prices, {self.adult_breakfast: {12}, self.child_breakfast: {6}}
        )
        self.assertEqual(
            self.breakfast._get_board_service_price(
                self.pricelist1, self.pms_property1, self.checkin, 2, 1
            ),
            30,
        )

    def test_children_price_extra(self):
        """
        Without pricelist rules, the variant for children takes the price of
        the board service plus the extra of its Guest value.
        """
        # ARRANGE
        self.breakfast.attribute_line_ids.product_template_value_ids.filtered(
            lambda value: value.product_attribute_value_id
            == self.env.ref("pms.product_attribute_value_board_guest_child")
        ).price_extra = -4
        # ACT
        reservation = self._create_reservation(
            adults=2, children=1, board_service_id=self.breakfast.id
        )
        # ASSERT
        child_service = reservation.service_ids.filtered(
            lambda service: service.product_id == self.child_breakfast
        )
        self.assertEqual(set(child_service.service_line_ids.mapped("price_unit")), {6})

    # CONFIGURATION
    def test_board_service_only_takes_the_guest_attribute(self):
        """
        A board service can't have other attributes: a reservation couldn't
        tell which variant a guest consumes.
        """
        # ARRANGE
        size = self.env["product.attribute"].create(
            {
                "name": "Size",
                "value_ids": [(0, 0, {"name": "S"}), (0, 0, {"name": "L"})],
            }
        )
        # ACT & ASSERT
        with self.assertRaisesRegex(ValidationError, "can only have the attribute"):
            self.breakfast.attribute_line_ids = [
                (
                    0,
                    0,
                    {
                        "attribute_id": size.id,
                        "value_ids": [(6, 0, size.value_ids.ids)],
                    },
                )
            ]

    def test_room_only_is_protected(self):
        """
        Room Only can't be deleted, have variants or stop being a board service.
        """
        with self.assertRaisesRegex(
            UserError, "can't be deleted"
        ), self.env.cr.savepoint():
            self.board_service_room_only.unlink()
        with self.assertRaisesRegex(
            ValidationError, "must be a board service"
        ), self.env.cr.savepoint():
            self.board_service_room_only.is_board_service = False
        with self.assertRaisesRegex(
            ValidationError, "can't have variants"
        ), self.env.cr.savepoint():
            self.board_service_room_only.attribute_line_ids = [
                (
                    0,
                    0,
                    {
                        "attribute_id": self.env.ref(
                            "pms.product_attribute_board_guest"
                        ).id,
                        "value_ids": [
                            (
                                6,
                                0,
                                [
                                    self.env.ref(
                                        "pms.product_attribute_value_board_guest_adult"
                                    ).id
                                ],
                            )
                        ],
                    },
                )
            ]

    def test_new_pricelist_sells_room_only(self):
        """
        A new pricelist sells rooms without board service.
        """
        pricelist = self.env["product.pricelist"].create(
            {
                "name": "New pricelist",
                "availability_plan_id": self.availability_plan1.id,
                "is_pms_available": True,
            }
        )
        self.assertEqual(pricelist.board_service_ids, self.board_service_room_only)

    def test_pricelist_default_board_service_must_be_sold(self):
        """
        The default board service of a pricelist must be one of its own.
        """
        half_board = self._create_board_service("Half Board")
        with self.assertRaisesRegex(ValidationError, "must be one of"):
            self.pricelist1.default_board_service_id = half_board

    def test_pricelist_without_room_only_needs_default(self):
        """
        A pricelist that doesn't sell Room Only must say which board service
        its reservations include.
        """
        with self.assertRaisesRegex(
            ValidationError, "needs a default"
        ), self.env.cr.savepoint():
            self.pricelist1.board_service_ids = [(6, 0, self.breakfast.ids)]
        self.pricelist1.write(
            {
                "board_service_ids": [(6, 0, self.breakfast.ids)],
                "default_board_service_id": self.breakfast.id,
            }
        )

    def test_room_only_cant_be_the_default(self):
        """
        Room Only is the absence of a board service, so it isn't a default.
        """
        with self.assertRaisesRegex(ValidationError, "leave the default empty"):
            self.pricelist1.default_board_service_id = self.board_service_room_only

    # DEFAULT OF THE RESERVATION
    def test_reservation_takes_the_default_of_the_pricelist(self):
        """
        A reservation includes the default board service of its pricelist.
        """
        # ARRANGE
        self.pricelist1.default_board_service_id = self.breakfast
        # ACT
        reservation = self._create_reservation()
        # ASSERT
        self.assertEqual(reservation.board_service_id, self.breakfast)
        self.assertTrue(reservation.service_ids.filtered("is_board_service"))

    def test_reservation_keeps_the_board_service_chosen(self):
        """
        Once chosen, even to sell Room Only, the board service of the
        reservation doesn't come back to the default of the pricelist.
        """
        # ARRANGE
        self.pricelist1.default_board_service_id = self.breakfast
        reservation = self._create_reservation()
        pricelist2 = self.env["product.pricelist"].create(
            {
                "name": "Pricelist 2",
                "availability_plan_id": self.availability_plan1.id,
                "is_pms_available": True,
                "board_service_ids": [
                    (6, 0, (self.board_service_room_only | self.breakfast).ids)
                ],
                "default_board_service_id": self.breakfast.id,
            }
        )
        # ACT
        reservation.board_service_id = False
        reservation.pricelist_id = pricelist2
        # ASSERT
        self.assertTrue(reservation.board_service_manual)
        self.assertFalse(reservation.board_service_id)
        self.assertFalse(reservation.service_ids.filtered("is_board_service"))

    def test_default_closed_for_the_stay_is_not_applied(self):
        """
        The default of the pricelist isn't applied to a stay with a night on
        which the availability plan closes it.
        """
        # ARRANGE
        self.pricelist1.default_board_service_id = self.breakfast
        self.env["pms.availability.plan.board.rule"].create(
            {
                "availability_plan_id": self.availability_plan1.id,
                "pms_property_id": self.pms_property1.id,
                "board_service_id": self.breakfast.id,
                "date_from": self.checkin + datetime.timedelta(days=1),
                "date_to": self.checkin + datetime.timedelta(days=1),
            }
        )
        # ACT
        reservation = self._create_reservation()
        # ASSERT
        self.assertFalse(reservation.board_service_id)
        self.assertNotIn(self.breakfast, reservation.allowed_board_service_ids)

    # CLOSINGS
    def _close(self, board_service, date_from, date_to, closed=True):
        return self.env["pms.availability.plan.board.rule"].create(
            {
                "availability_plan_id": self.availability_plan1.id,
                "pms_property_id": self.pms_property1.id,
                "board_service_id": board_service.id,
                "date_from": date_from,
                "date_to": date_to,
                "closed": closed,
            }
        )

    def _available(self, checkin, checkout):
        return self.pricelist1._get_available_board_services(
            self.pms_property1, checkin, checkout
        )

    def test_closing_room_only_forces_a_board_service(self):
        """
        Closing Room Only on some dates leaves only the board services.
        """
        # ARRANGE
        day = datetime.timedelta(days=1)
        self._close(self.board_service_room_only, self.checkin, self.checkin + day)
        # ACT & ASSERT
        self.assertEqual(self._available(self.checkin, self.checkout), self.breakfast)
        self.assertEqual(
            self._available(self.checkout, self.checkout + day),
            self.board_service_room_only | self.breakfast,
        )

    def test_closing_on_checkout_night_does_not_apply(self):
        """
        The night of the checkout isn't part of the stay.
        """
        # ARRANGE
        self._close(self.breakfast, self.checkout, self.checkout)
        # ACT & ASSERT
        self.assertIn(self.breakfast, self._available(self.checkin, self.checkout))

    def test_later_rule_reopens_a_closing(self):
        """
        The last rule written decides each night, so a rule not closed
        reopens what an earlier one closes.
        """
        # ARRANGE
        day = datetime.timedelta(days=1)
        self._close(self.breakfast, self.checkin - 10 * day, self.checkout + 10 * day)
        self._close(self.breakfast, self.checkin, self.checkout - day, closed=False)
        # ACT & ASSERT
        self.assertIn(self.breakfast, self._available(self.checkin, self.checkout))
        self.assertNotIn(
            self.breakfast, self._available(self.checkin, self.checkout + day)
        )

    def test_board_service_of_another_property_is_not_available(self):
        """
        A pricelist only sells, in a property, the board services available
        for it.
        """
        # ARRANGE
        pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        dinner = self._create_board_service(
            "Dinner", pms_property_ids=[pms_property2.id]
        )
        self.pricelist1.board_service_ids = [(4, dinner.id)]
        # ACT & ASSERT
        self.assertNotIn(dinner, self._available(self.checkin, self.checkout))
        self.assertIn(
            dinner,
            self.pricelist1._get_available_board_services(
                pms_property2, self.checkin, self.checkout
            ),
        )
