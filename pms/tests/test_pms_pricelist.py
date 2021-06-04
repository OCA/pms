import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import common, tagged


@tagged("standard", "nice")
class TestPmsPricelist(common.SavepointCase):
    def create_common_scenario(self):
        # sequences
        self.folio_sequence = self.env["ir.sequence"].create(
            {
                "name": "PMS Folio",
                "code": "pms.folio",
                "padding": 4,
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        self.reservation_sequence = self.env["ir.sequence"].create(
            {
                "name": "PMS Reservation",
                "code": "pms.reservation",
                "padding": 4,
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        self.checkin_sequence = self.env["ir.sequence"].create(
            {
                "name": "PMS Checkin",
                "code": "pms.checkin.partner",
                "padding": 4,
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        # create property
        self.property1 = self.env["pms.property"].create(
            {
                "name": "Property_1",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )

        self.property2 = self.env["pms.property"].create(
            {
                "name": "Property_2",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )

        self.property3 = self.env["pms.property"].create(
            {
                "name": "Property_3",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )
        self.room_type_class = self.env["pms.room.type.class"].create(
            {"name": "Room Class", "default_code": "ROOM"}
        )

        self.room_type = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.property1.id, self.property2.id],
                "name": "Single",
                "default_code": "SIN",
                "class_id": self.room_type_class.id,
                "list_price": 30,
            }
        )

        # pms.room
        self.room1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.property1.id,
                "name": "Single 101",
                "room_type_id": self.room_type.id,
                "capacity": 2,
            }
        )

        self.pricelist = self.env["product.pricelist"].create(
            {
                "name": "pricelist_1",
                "pms_property_ids": [self.property1.id, self.property2.id],
            }
        )
        # product.product 1
        self.test_service_breakfast = self.env["product.product"].create(
            {"name": "Test Breakfast"}
        )

        # pms.board.service
        self.test_board_service_only_breakfast = self.env["pms.board.service"].create(
            {
                "name": "Test Only Breakfast",
                "default_code": "CB1",
            }
        )
        # pms.board.service.line
        self.board_service_line_single_1 = self.env["pms.board.service.line"].create(
            {
                "product_id": self.test_service_breakfast.id,
                "pms_board_service_id": self.test_board_service_only_breakfast.id,
            }
        )

        # pms.board.service.room.type
        self.test_board_service_single = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type.id,
                "pms_board_service_id": self.test_board_service_only_breakfast.id,
            }
        )

        self.partner1 = self.env["res.partner"].create({"name": "Carles"})

    def test_advanced_pricelist_exists(self):

        # ARRANGE
        key = "product.product_pricelist_setting"
        value = "advanced"

        # ACT
        found_value = self.env["ir.config_parameter"].sudo().get_param(key)

        # ASSERT
        self.assertEqual(found_value, value, "Parameter doesn't exist")

    def test_product_pricelist_setting_modified(self):

        # ARRANGE
        key = "product.product_pricelist_setting"
        value = "basic"

        # ACT & ASSERT
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env["ir.config_parameter"].set_param(key, value)

    def test_product_pricelist_setting_unlink(self):

        # ARRANGE
        key = "product.product_pricelist_setting"
        value = "advanced"

        # ACT & ASSERT
        with self.assertRaises(ValidationError), self.cr.savepoint():
            self.env["ir.config_parameter"].search(
                [("key", "=", key), ("value", "=", value)]
            ).unlink()

    def test_check_property_pricelist(self):
        # ARRANGE
        self.create_common_scenario()
        # ACT & ASSERT
        with self.assertRaises(UserError):
            self.item1 = self.env["product.pricelist.item"].create(
                {
                    "name": "item_1",
                    "applied_on": "0_product_variant",
                    "product_id": self.room_type.product_id.id,
                    "date_start": datetime.datetime.today(),
                    "date_end": datetime.datetime.today() + datetime.timedelta(days=1),
                    "fixed_price": 40.0,
                    "pricelist_id": self.pricelist.id,
                    "pms_property_ids": [self.property3.id],
                }
            )

    def test_check_property_room_type(self):
        # ARRANGE
        self.create_common_scenario()
        # ACT
        self.pricelist1 = self.env["product.pricelist"].create(
            {
                "name": "pricelist_1",
                "pms_property_ids": [self.property1.id, self.property3.id],
            }
        )
        # ASSERT
        with self.assertRaises(UserError):
            self.item1 = self.env["product.pricelist.item"].create(
                {
                    "name": "item_1",
                    "applied_on": "0_product_variant",
                    "product_id": self.room_type.product_id.id,
                    "date_start": datetime.datetime.today(),
                    "date_end": datetime.datetime.today() + datetime.timedelta(days=1),
                    "fixed_price": 40.0,
                    "pricelist_id": self.pricelist1.id,
                    "pms_property_ids": [self.property3.id],
                }
            )

    def test_cancelation_rule_property(self):
        # ARRANGE
        self.create_common_scenario()
        Pricelist = self.env["product.pricelist"]
        # ACT
        self.cancelation_rule = self.env["pms.cancelation.rule"].create(
            {
                "name": "Cancelation Rule Test",
                "pms_property_ids": [self.property1.id, self.property3.id],
            }
        )
        # ASSERT
        with self.assertRaises(UserError):
            Pricelist.create(
                {
                    "name": "Pricelist Test",
                    "pms_property_ids": [self.property1.id, self.property2.id],
                    "cancelation_rule_id": self.cancelation_rule.id,
                }
            )

    def test_availability_plan_property_integrity(self):
        self.create_common_scenario()
        self.availability_plan = self.env["pms.availability.plan"].create(
            {"name": "Availability Plan", "pms_property_ids": [self.property1.id]}
        )
        with self.assertRaises(UserError):
            self.env["product.pricelist"].create(
                {
                    "name": "Pricelist",
                    "pms_property_ids": [self.property2.id],
                    "availability_plan_id": self.availability_plan.id,
                }
            )

    # board services pricelist items
    def test_board_service_pricelist_item_apply_sale_dates(self):
        # TEST CASE
        # Pricelist item is created to apply on board services at SALE date.
        # The reservation created take into account the board service
        # pricelist item created previously according to the SALE date.

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today()
        date_to = fields.date.today()
        expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist.id,
            "date_start": datetime.datetime.combine(
                date_from, datetime.datetime.min.time()
            ),
            "date_end": datetime.datetime.combine(
                date_to, datetime.datetime.max.time()
            ),
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.test_service_breakfast.id,
            "board_service_room_type_id": self.test_board_service_single.id,
            "fixed_price": expected_price,
            "pms_property_ids": [self.property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
                "board_service_room_id": self.test_board_service_single.id,
            }
        )
        # ASSERT
        self.assertEqual(
            reservation_created.service_ids.price_subtotal,
            expected_price,
            "The reservation created should take into account the board service"
            " pricelist item created previously according to the SALE date.",
        )

    def test_board_service_pricelist_item_not_apply_sale_dates(self):
        # TEST CASE
        # Pricelist item is created to apply on board services at SALE date.
        # The reservation created DONT take into account the board service pricelist
        # item created previously according to the SALE date.

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today() + datetime.timedelta(days=1)
        date_to = fields.date.today() + datetime.timedelta(days=1)
        not_expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist.id,
            "date_start": datetime.datetime.combine(
                date_from, datetime.datetime.min.time()
            ),
            "date_end": datetime.datetime.combine(
                date_to, datetime.datetime.max.time()
            ),
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.test_service_breakfast.id,
            "board_service_room_type_id": self.test_board_service_single.id,
            "fixed_price": not_expected_price,
            "pms_property_ids": [self.property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
                "board_service_room_id": self.test_board_service_single.id,
            }
        )
        # ASSERT
        self.assertNotEqual(
            reservation_created.service_ids.price_subtotal,
            not_expected_price,
            "The reservation created shouldnt take into account the board service pricelist"
            " item created previously according to the SALE date.",
        )

    def test_board_service_pricelist_item_apply_consumption_dates(self):
        # TEST CASE
        # Pricelist item is created to apply on board services
        # at CONSUMPTION date.
        # The reservation created take into account the board service
        # pricelist item created previously according to the CONSUMPTION date.

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today() + datetime.timedelta(days=1)
        date_to = fields.date.today() + datetime.timedelta(days=1)
        expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist.id,
            "date_start_consumption": date_from,
            "date_end_consumption": date_to,
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.test_service_breakfast.id,
            "board_service_room_type_id": self.test_board_service_single.id,
            "fixed_price": expected_price,
            "pms_property_ids": [self.property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
                "board_service_room_id": self.test_board_service_single.id,
            }
        )
        # ASSERT
        self.assertEqual(
            reservation_created.service_ids.price_subtotal,
            expected_price,
            "The reservation created should take into account the board service"
            " pricelist item created previously according to the CONSUMPTION date.",
        )

    def test_board_service_pricelist_item_not_apply_consumption_dates(self):
        # TEST CASE
        # Pricelist item is created to apply on board services
        # at CONSUMPTION date.
        # The reservation created DONT take into account the board service
        # pricelist item created previously according to the CONSUMPTION date.

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today() + datetime.timedelta(days=2)
        date_to = fields.date.today() + datetime.timedelta(days=2)
        not_expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist.id,
            "date_start": datetime.datetime.combine(
                date_from, datetime.datetime.min.time()
            ),
            "date_end": datetime.datetime.combine(
                date_to, datetime.datetime.max.time()
            ),
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.test_service_breakfast.id,
            "board_service_room_type_id": self.test_board_service_single.id,
            "fixed_price": not_expected_price,
            "pms_property_ids": [self.property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
                "board_service_room_id": self.test_board_service_single.id,
            }
        )
        # ASSERT
        self.assertNotEqual(
            reservation_created.service_ids.price_subtotal,
            not_expected_price,
            "The reservation created shouldnt take into account the board service"
            " pricelist item created previously according to the CONSUMPTION date.",
        )

    # room types pricelist items
    def test_room_type_pricelist_item_apply_sale_dates(self):
        # TEST CASE
        # Pricelist item is created to apply on room types
        # at SALE date.
        # The reservation created take into account the room type
        # pricelist item created previously according to the SALE date.

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today()
        date_to = fields.date.today()
        expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist.id,
            "date_start": datetime.datetime.combine(
                date_from, datetime.datetime.min.time()
            ),
            "date_end": datetime.datetime.combine(
                date_to, datetime.datetime.max.time()
            ),
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.room_type.product_id.id,
            "fixed_price": expected_price,
            "pms_property_ids": [self.property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
            }
        )
        # ASSERT
        self.assertEqual(
            reservation_created.price_subtotal,
            expected_price,
            "The reservation created should take into account the room type"
            " pricelist item created previously according to the SALE date.",
        )

    def test_room_type_pricelist_item_not_apply_sale_dates(self):
        # TEST CASE
        # Pricelist item is created to apply on room types
        # at SALE date.
        # The reservation created DONT take into account the room type
        # pricelist item created previously according to the SALE date.

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today() + datetime.timedelta(days=1)
        date_to = fields.date.today() + datetime.timedelta(days=1)
        not_expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist.id,
            "date_start": datetime.datetime.combine(
                date_from, datetime.datetime.min.time()
            ),
            "date_end": datetime.datetime.combine(
                date_to, datetime.datetime.max.time()
            ),
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.room_type.product_id.id,
            "fixed_price": not_expected_price,
            "pms_property_ids": [self.property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
            }
        )
        # ASSERT
        self.assertNotEqual(
            reservation_created.price_subtotal,
            not_expected_price,
            "The reservation created shouldnt take into account the room type"
            " pricelist item created previously according to the SALE date.",
        )

    def test_room_type_pricelist_item_apply_consumption_dates(self):
        # TEST CASE
        # Pricelist item is created to apply on room types
        # at CONSUMPTION date.
        # The reservation created take into account the room type
        # pricelist item created previously according to the CONSUMPTION date.

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today() + datetime.timedelta(days=1)
        date_to = fields.date.today() + datetime.timedelta(days=1)
        expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist.id,
            "date_start_consumption": date_from,
            "date_end_consumption": date_to,
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.room_type.product_id.id,
            "fixed_price": expected_price,
            "pms_property_ids": [self.property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
            }
        )
        # ASSERT
        self.assertEqual(
            reservation_created.price_subtotal,
            expected_price,
            "The reservation created should take into account the room type"
            " pricelist item created previously according to the CONSUMPTION date.",
        )

    def test_room_type_pricelist_item_not_apply_consumption_dates(self):
        # TEST CASE
        # Pricelist item is created to apply on room types
        # at CONSUMPTION date.
        # The reservation created DONT take into account the room type
        # pricelist item created previously according to the CONSUMPTION date.

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today() + datetime.timedelta(days=2)
        date_to = fields.date.today() + datetime.timedelta(days=2)
        not_expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist.id,
            "date_start": datetime.datetime.combine(
                date_from, datetime.datetime.min.time()
            ),
            "date_end": datetime.datetime.combine(
                date_to, datetime.datetime.max.time()
            ),
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.room_type.product_id.id,
            "fixed_price": not_expected_price,
            "pms_property_ids": [self.property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
            }
        )
        # ASSERT
        self.assertNotEqual(
            reservation_created.price_subtotal,
            not_expected_price,
            "The reservation created shouldnt take into account the room type"
            " pricelist item created previously according to the CONSUMPTION date.",
        )

    # services pricelist items
    def test_service_pricelist_item_apply_sale_dates(self):
        # TEST CASE
        # Pricelist item is created to apply on services at SALE date.
        # The reservation created take into account the service
        # pricelist item created previously according to the SALE date.

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today()
        date_to = fields.date.today()
        expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist.id,
            "date_start": datetime.datetime.combine(
                date_from, datetime.datetime.min.time()
            ),
            "date_end": datetime.datetime.combine(
                date_to, datetime.datetime.max.time()
            ),
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.test_service_breakfast.id,
            "fixed_price": expected_price,
            "pms_property_ids": [self.property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
                "service_ids": [(0, 0, {"product_id": self.test_service_breakfast.id})],
            }
        )
        # ASSERT
        self.assertEqual(
            reservation_created.service_ids.price_subtotal,
            expected_price,
            "The reservation created should take into account the service"
            " pricelist item created previously according to the SALE date.",
        )

    def test_service_pricelist_item_not_apply_sale_dates(self):
        # TEST CASE
        # Pricelist item is created to apply on services at SALE date.
        # The reservation created DONT take into account the service pricelist
        # item created previously according to the SALE date.

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today() + datetime.timedelta(days=1)
        date_to = fields.date.today() + datetime.timedelta(days=1)
        not_expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist.id,
            "date_start": datetime.datetime.combine(
                date_from, datetime.datetime.min.time()
            ),
            "date_end": datetime.datetime.combine(
                date_to, datetime.datetime.max.time()
            ),
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.test_service_breakfast.id,
            "fixed_price": not_expected_price,
            "pms_property_ids": [self.property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
                "service_ids": [(0, 0, {"product_id": self.test_service_breakfast.id})],
            }
        )
        # ASSERT
        self.assertNotEqual(
            reservation_created.service_ids.price_subtotal,
            not_expected_price,
            "The reservation created shouldnt take into account the service pricelist"
            " item created previously according to the SALE date.",
        )

    def test_service_pricelist_item_apply_consumption_dates(self):
        # TEST CASE
        # Pricelist item is created to apply on services at CONSUMPTION date.
        # The reservation created take into account the service
        # pricelist item created previously according to the CONSUMPTION date.

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today() + datetime.timedelta(days=1)
        date_to = fields.date.today() + datetime.timedelta(days=1)
        expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist.id,
            "date_start_consumption": date_from,
            "date_end_consumption": date_to,
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.test_service_breakfast.id,
            "fixed_price": expected_price,
            "pms_property_ids": [self.property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
                "service_ids": [(0, 0, {"product_id": self.test_service_breakfast.id})],
            }
        )
        # ASSERT
        self.assertEqual(
            reservation_created.service_ids.price_subtotal,
            expected_price,
            "The reservation created should take into account the service"
            " pricelist item created previously according to the CONSUMPTION date.",
        )

    def test_service_pricelist_item_not_apply_consumption_dates(self):
        # TEST CASE
        # Pricelist item is created to apply on services at CONSUMPTION date.
        # The reservation created DONT take into account the service pricelist
        # item created previously according to the CONSUMPTION date.

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today() + datetime.timedelta(days=2)
        date_to = fields.date.today() + datetime.timedelta(days=2)
        not_expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist.id,
            "date_start": datetime.datetime.combine(
                date_from, datetime.datetime.min.time()
            ),
            "date_end": datetime.datetime.combine(
                date_to, datetime.datetime.max.time()
            ),
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.test_service_breakfast.id,
            "fixed_price": not_expected_price,
            "pms_property_ids": [self.property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
                "service_ids": [(0, 0, {"product_id": self.test_service_breakfast.id})],
            }
        )
        # ASSERT
        self.assertNotEqual(
            reservation_created.service_ids.price_subtotal,
            not_expected_price,
            "The reservation created shouldnt take into account the service pricelist "
            "item created previously according to the CONSUMPTION date.",
        )

    @freeze_time("2000-01-01")
    def test_pricelist_daily_failed(self):
        self.create_common_scenario()
        test_cases = [
            {
                "compute_price": "fixed",
                "pms_property_ids": [self.property1.id, self.property2.id],
                "date_start_consumption": datetime.datetime.now(),
                "date_end_consumption": datetime.datetime.today()
                + datetime.timedelta(days=1),
            },
            {
                "compute_price": "fixed",
                "pms_property_ids": False,
                "date_start_consumption": datetime.datetime.now(),
                "date_end_consumption": datetime.datetime.today()
                + datetime.timedelta(days=1),
            },
            {
                "compute_price": "percentage",
                "pms_property_ids": [self.property1.id],
                "date_start_consumption": datetime.datetime.now(),
                "date_end_consumption": datetime.datetime.today()
                + datetime.timedelta(days=1),
            },
            {
                "compute_price": "percentage",
                "pms_property_ids": [self.property1.id, self.property2.id],
                "date_start_consumption": datetime.datetime.now(),
                "date_end_consumption": datetime.datetime.today()
                + datetime.timedelta(days=1),
            },
            {
                "compute_price": "percentage",
                "pms_property_ids": False,
                "date_start_consumption": datetime.datetime.now(),
                "date_end_consumption": datetime.datetime.today()
                + datetime.timedelta(days=1),
            },
            {
                "compute_price": "fixed",
                "pms_property_ids": [self.property1.id],
                "date_start_consumption": datetime.datetime.now(),
                "date_end_consumption": datetime.datetime.today()
                + datetime.timedelta(days=3),
            },
        ]

        for tc in test_cases:
            with self.subTest(k=tc):
                with self.assertRaises(ValidationError):
                    self.room_type.pms_property_ids = tc["pms_property_ids"]
                    item = self.env["product.pricelist.item"].create(
                        {
                            "pms_property_ids": tc["pms_property_ids"],
                            "compute_price": tc["compute_price"],
                            "applied_on": "0_product_variant",
                            "product_id": self.room_type.product_id.id,
                            "date_start_consumption": tc["date_start_consumption"],
                            "date_end_consumption": tc["date_end_consumption"],
                        }
                    )
                    self.pricelist_test = self.env["product.pricelist"].create(
                        {
                            "name": "Pricelist test",
                            "pricelist_type": "daily",
                            "pms_property_ids": tc["pms_property_ids"],
                            "item_ids": [item.id],
                        }
                    )

    @freeze_time("2020-01-01")
    def test_pricelist_daily(self):
        self.create_common_scenario()
        self.room_type.pms_property_ids = (self.property1.id,)
        item = self.env["product.pricelist.item"].create(
            {
                "pms_property_ids": [self.property1.id],
                "compute_price": "fixed",
                "applied_on": "0_product_variant",
                "product_id": self.room_type.product_id.id,
                "date_start_consumption": datetime.date.today(),
                "date_end_consumption": datetime.date.today(),
            }
        )
        self.pricelist_test = self.env["product.pricelist"].create(
            {
                "name": "Pricelist test",
                "pricelist_type": "daily",
                "pms_property_ids": [self.property1.id],
                "item_ids": [item.id],
            }
        )
        self.assertTrue(self.pricelist_test, "Pricelist not created.")
