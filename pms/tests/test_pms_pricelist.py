import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import TestPms


@tagged("standard", "nice")
class TestPmsPricelist(TestPms):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pms_property2 = cls.env["pms.property"].create(
            {
                "name": "Property_2",
                "company_id": cls.env.ref("base.main_company").id,
                "default_pricelist_id": cls.env.ref("product.list0").id,
            }
        )

        cls.pms_property3 = cls.env["pms.property"].create(
            {
                "name": "Property_3",
                "company_id": cls.env.ref("base.main_company").id,
                "default_pricelist_id": cls.env.ref("product.list0").id,
            }
        )

        cls.room_type1 = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id, cls.pms_property2.id],
                "name": "Single",
                "default_code": "SIN",
                "class_id": cls.room_type_class1.id,
                "list_price": 30,
            }
        )

        # pms.room
        cls.room1 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Single 101",
                "room_type_id": cls.room_type1.id,
                "capacity": 2,
            }
        )

        cls.pricelist2 = cls.env["product.pricelist"].create(
            {
                "name": "pricelist_2",
                "pms_property_ids": [cls.pms_property1.id, cls.pms_property2.id],
                "availability_plan_id": cls.availability_plan1.id,
                "is_pms_available": True,
            }
        )
        # product.product 1
        cls.product1 = cls.env["product.product"].create(
            {"name": "Test Breakfast", "per_day": True, "consumed_on": "after"}
        )

        # pms.board.service
        cls.board_service1 = cls.env["pms.board.service"].create(
            {
                "name": "Test Only Breakfast",
                "default_code": "CB1",
            }
        )
        # pms.board.service.line
        cls.board_service_line1 = cls.env["pms.board.service.line"].create(
            {
                "product_id": cls.product1.id,
                "pms_board_service_id": cls.board_service1.id,
                "adults": True,
            }
        )

        # pms.board.service.room.type
        cls.board_service_room_type1 = cls.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": cls.room_type1.id,
                "pms_board_service_id": cls.board_service1.id,
                "pms_property_id": cls.pms_property1.id,
            }
        )

        cls.partner1 = cls.env["res.partner"].create({"name": "Carles"})

        # create a sale channel
        cls.sale_channel_direct1 = cls.env["pms.sale.channel"].create(
            {
                "name": "Door",
                "channel_type": "direct",
            }
        )

    @freeze_time("2000-01-01")
    def test_board_service_pricelist_item_apply_sale_dates(self):
        """
        Pricelist item is created to apply on board services at SALE date.
        The reservation created take into account the board service
        pricelist item created previously according to the SALE date.
        """
        # ARRANGE
        date_from = fields.date.today()
        date_to = fields.date.today()
        expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist2.id,
            "date_start": datetime.datetime.combine(
                date_from, datetime.datetime.min.time()
            ),
            "date_end": datetime.datetime.combine(
                date_to, datetime.datetime.max.time()
            ),
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.product1.id,
            "board_service_room_type_id": self.board_service_room_type1.id,
            "fixed_price": expected_price,
            "pms_property_ids": [self.pms_property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist2.id,
                "board_service_room_id": self.board_service_room_type1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # ASSERT
        self.assertEqual(
            reservation_created.service_ids.price_subtotal,
            expected_price,
            "The reservation created should take into account the board service"
            " pricelist item created previously according to the SALE date.",
        )

    @freeze_time("2000-01-01")
    def test_board_service_pricelist_item_not_apply_sale_dates(self):
        """
        Pricelist item is created to apply on board services at SALE date.
        The reservation created DONT take into account the board service pricelist
        item created previously according to the SALE date.
        """
        # ARRANGE
        date_from = fields.date.today() + datetime.timedelta(days=1)
        date_to = fields.date.today() + datetime.timedelta(days=1)
        not_expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist2.id,
            "date_start": datetime.datetime.combine(
                date_from, datetime.datetime.min.time()
            ),
            "date_end": datetime.datetime.combine(
                date_to, datetime.datetime.max.time()
            ),
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.product1.id,
            "board_service_room_type_id": self.board_service_room_type1.id,
            "fixed_price": not_expected_price,
            "pms_property_ids": [self.pms_property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist2.id,
                "board_service_room_id": self.board_service_room_type1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # ASSERT
        self.assertNotEqual(
            reservation_created.service_ids.price_subtotal,
            not_expected_price,
            "The reservation created shouldnt take into account the board "
            "service pricelist item created previously according to the SALE date.",
        )

    @freeze_time("2000-01-01")
    def test_board_service_pricelist_item_apply_consumption_dates(self):
        """
        Pricelist item is created to apply on board services
        at CONSUMPTION date.
        The reservation created take into account the board service
        pricelist item created previously according to the CONSUMPTION date.
        """
        # ARRANGE
        date_from = fields.date.today() + datetime.timedelta(days=2)
        date_to = fields.date.today() + datetime.timedelta(days=2)
        expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist2.id,
            "date_start_consumption": date_from,
            "date_end_consumption": date_to,
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.product1.id,
            "board_service_room_type_id": self.board_service_room_type1.id,
            "fixed_price": expected_price,
            "pms_property_ids": [self.pms_property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist2.id,
                "board_service_room_id": self.board_service_room_type1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # ASSERT
        self.assertEqual(
            reservation_created.service_ids.price_subtotal,
            expected_price,
            "The reservation created should take into account the board service"
            " pricelist item created previously according to the CONSUMPTION date.",
        )

    @freeze_time("2000-01-01")
    def test_board_service_pricelist_item_not_apply_consumption_dates(self):
        """
        Pricelist item is created to apply on board services
        at CONSUMPTION date.
        The reservation created DONT take into account the board service
        pricelist item created previously according to the CONSUMPTION date.
        """
        # ARRANGE
        date_from = fields.date.today() + datetime.timedelta(days=2)
        date_to = fields.date.today() + datetime.timedelta(days=2)
        not_expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist2.id,
            "date_start": datetime.datetime.combine(
                date_from, datetime.datetime.min.time()
            ),
            "date_end": datetime.datetime.combine(
                date_to, datetime.datetime.max.time()
            ),
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.product1.id,
            "board_service_room_type_id": self.board_service_room_type1.id,
            "fixed_price": not_expected_price,
            "pms_property_ids": [self.pms_property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist2.id,
                "board_service_room_id": self.board_service_room_type1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # ASSERT
        self.assertNotEqual(
            reservation_created.service_ids.price_subtotal,
            not_expected_price,
            "The reservation created shouldnt take into account the board service"
            " pricelist item created previously according to the CONSUMPTION date.",
        )

    @freeze_time("2000-01-01")
    def test_room_type_pricelist_item_apply_sale_dates(self):
        """
        Pricelist item is created to apply on room types
        at SALE date.
        The reservation created take into account the room type
        pricelist item created previously according to the SALE date.
        """
        # ARRANGE
        date_from = fields.date.today()
        date_to = fields.date.today()
        expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist2.id,
            "date_start": datetime.datetime.combine(
                date_from, datetime.datetime.min.time()
            ),
            "date_end": datetime.datetime.combine(
                date_to, datetime.datetime.max.time()
            ),
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.room_type1.product_id.id,
            "fixed_price": expected_price,
            "pms_property_ids": [self.pms_property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist2.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # ASSERT
        self.assertEqual(
            reservation_created.price_subtotal,
            expected_price,
            "The reservation created should take into account the room type"
            " pricelist item created previously according to the SALE date.",
        )

    @freeze_time("2000-01-01")
    def test_room_type_pricelist_item_not_apply_sale_dates(self):
        """
        Pricelist item is created to apply on room types
        at SALE date.
        The reservation created DONT take into account the room type
        pricelist item created previously according to the SALE date.
        """
        # ARRANGE
        date_from = fields.date.today() + datetime.timedelta(days=1)
        date_to = fields.date.today() + datetime.timedelta(days=1)
        not_expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist2.id,
            "date_start": datetime.datetime.combine(
                date_from, datetime.datetime.min.time()
            ),
            "date_end": datetime.datetime.combine(
                date_to, datetime.datetime.max.time()
            ),
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.room_type1.product_id.id,
            "fixed_price": not_expected_price,
            "pms_property_ids": [self.pms_property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist2.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # ASSERT
        self.assertNotEqual(
            reservation_created.price_subtotal,
            not_expected_price,
            "The reservation created shouldnt take into account the room type"
            " pricelist item created previously according to the SALE date.",
        )

    @freeze_time("2000-01-01")
    def test_room_type_pricelist_item_apply_consumption_dates(self):
        """
        Pricelist item is created to apply on room types
        at CONSUMPTION date.
        The reservation created take into account the room type
        pricelist item created previously according to the CONSUMPTION date.
        """
        # ARRANGE
        date_from = fields.date.today() + datetime.timedelta(days=1)
        date_to = fields.date.today() + datetime.timedelta(days=1)
        expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist2.id,
            "date_start_consumption": date_from,
            "date_end_consumption": date_to,
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.room_type1.product_id.id,
            "fixed_price": expected_price,
            "pms_property_ids": [self.pms_property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist2.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # ASSERT
        self.assertEqual(
            reservation_created.price_subtotal,
            expected_price,
            "The reservation created should take into account the room type"
            " pricelist item created previously according to the CONSUMPTION date.",
        )

    @freeze_time("2000-01-01")
    def test_room_type_pricelist_item_not_apply_consumption_dates(self):
        """
        Pricelist item is created to apply on room types
        at CONSUMPTION date.
        The reservation created DONT take into account the room type
        pricelist item created previously according to the CONSUMPTION date.
        """
        # ARRANGE
        date_from = fields.date.today() + datetime.timedelta(days=2)
        date_to = fields.date.today() + datetime.timedelta(days=2)
        not_expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist2.id,
            "date_start": datetime.datetime.combine(
                date_from, datetime.datetime.min.time()
            ),
            "date_end": datetime.datetime.combine(
                date_to, datetime.datetime.max.time()
            ),
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.room_type1.product_id.id,
            "fixed_price": not_expected_price,
            "pms_property_ids": [self.pms_property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist2.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # ASSERT
        self.assertNotEqual(
            reservation_created.price_subtotal,
            not_expected_price,
            "The reservation created shouldnt take into account the room type"
            " pricelist item created previously according to the CONSUMPTION date.",
        )

    @freeze_time("2000-01-01")
    def test_service_pricelist_item_apply_sale_dates(self):
        """
        Pricelist item is created to apply on services at SALE date.
        The reservation created take into account the service
        pricelist item created previously according to the SALE date.
        """
        # ARRANGE
        date_from = fields.date.today()
        date_to = fields.date.today()
        expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist2.id,
            "date_start": datetime.datetime.combine(
                date_from, datetime.datetime.min.time()
            ),
            "date_end": datetime.datetime.combine(
                date_to, datetime.datetime.max.time()
            ),
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.product1.id,
            "fixed_price": expected_price,
            "pms_property_ids": [self.pms_property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist2.id,
                "service_ids": [(0, 0, {"product_id": self.product1.id})],
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # ASSERT
        self.assertEqual(
            reservation_created.service_ids.price_subtotal,
            expected_price,
            "The reservation created should take into account the service"
            " pricelist item created previously according to the SALE date.",
        )

    @freeze_time("2000-01-01")
    def test_service_pricelist_item_not_apply_sale_dates(self):
        """
        Pricelist item is created to apply on services at SALE date.
        The reservation created DONT take into account the service pricelist
        item created previously according to the SALE date.
        """
        # ARRANGE
        date_from = fields.date.today() + datetime.timedelta(days=1)
        date_to = fields.date.today() + datetime.timedelta(days=1)
        not_expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist2.id,
            "date_start": datetime.datetime.combine(
                date_from, datetime.datetime.min.time()
            ),
            "date_end": datetime.datetime.combine(
                date_to, datetime.datetime.max.time()
            ),
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.product1.id,
            "fixed_price": not_expected_price,
            "pms_property_ids": [self.pms_property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist2.id,
                "service_ids": [(0, 0, {"product_id": self.product1.id})],
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # ASSERT
        self.assertNotEqual(
            reservation_created.service_ids.price_subtotal,
            not_expected_price,
            "The reservation created shouldnt take into account the service pricelist"
            " item created previously according to the SALE date.",
        )

    @freeze_time("2000-01-01")
    def test_service_pricelist_item_apply_consumption_dates(self):
        """
        Pricelist item is created to apply on services at CONSUMPTION date.
        The reservation created take into account the service
        pricelist item created previously according to the CONSUMPTION date.
        """
        # ARRANGE
        date_from = fields.date.today() + datetime.timedelta(days=2)
        date_to = fields.date.today() + datetime.timedelta(days=2)
        expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist2.id,
            "date_start_consumption": date_from,
            "date_end_consumption": date_to,
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.product1.id,
            "fixed_price": expected_price,
            "pms_property_ids": [self.pms_property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now() + datetime.timedelta(days=1),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=2),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist2.id,
                "service_ids": [(0, 0, {"product_id": self.product1.id})],
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # ASSERT
        self.assertEqual(
            reservation_created.service_ids.price_subtotal,
            expected_price,
            "The reservation created should take into account the service"
            " pricelist item created previously according to the CONSUMPTION date.",
        )

    @freeze_time("2000-01-01")
    def test_service_pricelist_item_not_apply_consumption_dates(self):
        """
        Pricelist item is created to apply on services at CONSUMPTION date.
        The reservation created DONT take into account the service pricelist
        item created previously according to the CONSUMPTION date.
        """
        # ARRANGE
        date_from = fields.date.today() + datetime.timedelta(days=2)
        date_to = fields.date.today() + datetime.timedelta(days=2)
        not_expected_price = 1000.0
        vals = {
            "pricelist_id": self.pricelist2.id,
            "date_start": datetime.datetime.combine(
                date_from, datetime.datetime.min.time()
            ),
            "date_end": datetime.datetime.combine(
                date_to, datetime.datetime.max.time()
            ),
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.product1.id,
            "fixed_price": not_expected_price,
            "pms_property_ids": [self.pms_property1.id],
        }
        self.env["product.pricelist.item"].create(vals)
        # ACT
        reservation_created = self.env["pms.reservation"].create(
            {
                "partner_id": self.partner1.id,
                "checkin": datetime.datetime.now(),
                "checkout": datetime.datetime.now() + datetime.timedelta(days=1),
                "preferred_room_id": self.room1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist2.id,
                "service_ids": [(0, 0, {"product_id": self.product1.id})],
                "sale_channel_origin_id": self.sale_channel_direct1.id,
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
    def _test_inconsistencies_pricelist_daily(self):
        """
        Test cases to verify that a daily pricelist cannot be created because:
        (Test case1): item has two properties and a items daily pricelist only
                      can has a one property.
        (Test case2): item has all properties(pms_property_ids = False indicates
                      all properties)and a items daily pricelist only
                      can has a one property.
        (Test case3): item compute_price is 'percentage' and only can be 'fixed'
                      for items daily pricelist.
        (Test case4): item compute_price is 'percentage' and has two properties
                      but compute_price can only be fixed and can only have one
                      property for items daily pricelist.
        (Test case5): item compute_price is 'percentage' and has all properties
                      (pms_property_ids = False indicates all properties)but
                      compute_pricecan only be fixed and can only have one property for
                      items daily pricelist.
        (Test case6): The difference of days between date_start_consumption and
                      date_end_consumption is three and the items of a daily pricelist
                      can only be one.
        """
        test_cases = [
            {
                "compute_price": "fixed",
                "pms_property_ids": [self.pms_property1.id, self.pms_property2.id],
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
                "pms_property_ids": [self.pms_property1.id],
                "date_start_consumption": datetime.datetime.now(),
                "date_end_consumption": datetime.datetime.today()
                + datetime.timedelta(days=1),
            },
            {
                "compute_price": "percentage",
                "pms_property_ids": [self.pms_property1.id, self.pms_property2.id],
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
                "pms_property_ids": [self.pms_property1.id],
                "date_start_consumption": datetime.datetime.now(),
                "date_end_consumption": datetime.datetime.today()
                + datetime.timedelta(days=3),
            },
        ]

        for tc in test_cases:
            with self.subTest(k=tc):
                with self.assertRaises(
                    ValidationError,
                    msg="Item only can has one property, the compute price only can"
                    "be fixed and the difference between date_start_consumption"
                    "and date_end_consumption only can be 1",
                ):
                    self.room_type1.pms_property_ids = tc["pms_property_ids"]
                    item = self.env["product.pricelist.item"].create(
                        {
                            "pms_property_ids": tc["pms_property_ids"],
                            "compute_price": tc["compute_price"],
                            "applied_on": "0_product_variant",
                            "product_id": self.room_type1.product_id.id,
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
                            "availability_plan_id": self.availability_plan1.id,
                            "is_pms_available": True,
                        }
                    )

    @freeze_time("2020-01-01")
    def test_consistency_pricelist_daily(self):
        """
        Test to verify that a daily pricelist is created.
        Create a pricelist item with a property, the value of compute_price is
        fixed and date_start_consumption date_end_consumption has the same value
        """
        self.room_type1.pms_property_ids = (self.pms_property1.id,)
        item = self.env["product.pricelist.item"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "compute_price": "fixed",
                "applied_on": "0_product_variant",
                "product_id": self.room_type1.product_id.id,
                "date_start_consumption": datetime.date.today(),
                "date_end_consumption": datetime.date.today(),
            }
        )
        self.pricelist_test = self.env["product.pricelist"].create(
            {
                "name": "Pricelist test",
                "pricelist_type": "daily",
                "pms_property_ids": [self.pms_property1.id],
                "item_ids": [item.id],
                "availability_plan_id": self.availability_plan1.id,
                "is_pms_available": True,
            }
        )
        self.assertTrue(self.pricelist_test, "Pricelist not created.")

    @freeze_time("2000-01-01")
    def test_simple_price_without_items(self):
        """
        Test case for no items applied in a reservation.
        """

        # ARRANGE
        self.room_type = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id, self.pms_property2.id],
                "name": "Single",
                "default_code": "S",
                "class_id": self.room_type_class1.id,
                "list_price": 30,
            }
        )

        self.room = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Single 1",
                "room_type_id": self.room_type.id,
            }
        )
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": datetime.datetime.today(),
                "checkout": datetime.datetime.today() + datetime.timedelta(days=3),
                "preferred_room_id": self.room.id,
                "pms_property_id": self.pms_property1.id,
                "partner_id": self.partner1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # ACT
        n_days = (reservation.checkout - reservation.checkin).days
        expected_price = self.room.room_type_id.list_price * n_days

        # ASSERT
        self.assertEqual(
            expected_price, reservation.price_subtotal, "The price is not as expected"
        )

    @freeze_time("2022-01-01")
    def test_items_sort(self):
        """
        Test cases to verify the order for each field considered individually
        Test cases to prioritize fields over other fields:
            1. applied_on
            2. date
            3. date consumption
            4. num. properties
            5. id
            - tie
            - no [date_start|date_end|date_start_consumption|date_end_consumption]
        """
        # ARRANGE
        self.product_category = self.env["product.category"].create(
            {"name": "Category1"}
        )
        self.product_template = self.env["product.template"].create(
            {"name": "Template1"}
        )
        self.room_type = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id, self.pms_property2.id],
                "name": "Single",
                "default_code": "SGL",
                "class_id": self.room_type_class1.id,
                "list_price": 30,
            }
        )

        self.room = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "101",
                "room_type_id": self.room_type.id,
            }
        )
        properties = self.room_type.product_id.pms_property_ids.ids
        test_cases = [
            {
                "name": "sorting num. properties",
                "expected_price": 50.0 * 3,
                "items": [
                    {
                        "pricelist_id": self.pricelist1.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "fixed_price": 60.0,
                    },
                    {
                        "pricelist_id": self.pricelist1.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "pms_property_ids": [self.pms_property1.id],
                        "fixed_price": 50.0,
                    },
                ],
            },
            {
                "name": "no SALE DATE START",
                "expected_price": 40.0 * 3,
                "items": [
                    {
                        "pricelist_id": self.pricelist1.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_end": datetime.datetime.now()
                        + datetime.timedelta(days=1),
                        "fixed_price": 40.0,
                        "pms_property_ids": properties,
                    },
                ],
            },
            {
                "name": "no SALE DATE END",
                "expected_price": 40.0 * 3,
                "items": [
                    {
                        "pricelist_id": self.pricelist1.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start": datetime.datetime.now(),
                        "fixed_price": 40.0,
                        "pms_property_ids": properties,
                    },
                ],
            },
            {
                "name": "no consumption DATE START",
                "expected_price": 40.0 + self.room_type.list_price * 2,
                "items": [
                    {
                        "pricelist_id": self.pricelist1.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_end_consumption": datetime.datetime.now(),
                        "fixed_price": 40.0,
                        "pms_property_ids": properties,
                    },
                ],
            },
            {
                "name": "no consumption DATE END",
                "expected_price": 40.0 * 3,
                "items": [
                    {
                        "pricelist_id": self.pricelist1.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start_consumption": datetime.datetime.now(),
                        "fixed_price": 40.0,
                        "pms_property_ids": properties,
                    },
                ],
            },
            {
                "name": "only applied consumption in one night",
                "expected_price": 40.0 + self.room_type.list_price * 2,
                "items": [
                    {
                        "pricelist_id": self.pricelist1.id,
                        "applied_on": "0_product_variant",
                        "product_id": self.room_type.product_id.id,
                        "date_start_consumption": datetime.datetime.now(),
                        "date_end_consumption": datetime.datetime.now(),
                        "fixed_price": 40.0,
                        "pms_property_ids": properties,
                    },
                ],
            },
        ]

        for tc in test_cases:
            with self.subTest(k=tc):
                # ARRANGE
                items = []
                for item in tc["items"]:
                    item = self.env["product.pricelist.item"].create(item)
                    items.append(item.id)

                # ACT
                reservation = self.env["pms.reservation"].create(
                    {
                        "partner_id": self.partner1.id,
                        "checkin": datetime.datetime.now(),
                        "checkout": datetime.datetime.now()
                        + datetime.timedelta(days=3),
                        "preferred_room_id": self.room.id,
                        "pms_property_id": self.pms_property1.id,
                        "pricelist_id": self.pricelist1.id,
                        "sale_channel_origin_id": self.sale_channel_direct1.id,
                    }
                )
                reservation_price = reservation.price_subtotal
                self.env["pms.reservation"].browse(reservation.id).unlink()
                self.env["product.pricelist.item"].browse(items).unlink()

                # ASSERT
                self.assertEqual(tc["expected_price"], reservation_price, tc["name"])
