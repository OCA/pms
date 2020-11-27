import datetime

from freezegun import freeze_time

from odoo.tests import common, tagged


@tagged("standard", "nice")
class TestPmsPricelistRules(common.TransactionCase):
    def create_common_scenario(self):
        self.product_template = self.env["product.template"].create(
            {"name": "Template1"}
        )
        self.product_category = self.env["product.category"].create(
            {"name": "Category1"}
        )

        self.restriction = self.env["pms.room.type.restriction"].create(
            {"name": "Restriction1"}
        )

        self.restriction2 = self.env["pms.room.type.restriction"].create(
            {"name": "Restriction2"}
        )
        self.property1 = self.env["pms.property"].create(
            {
                "name": "Property_1",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "default_restriction_id": self.restriction.id,
            }
        )

        self.property2 = self.env["pms.property"].create(
            {
                "name": "Property_2",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
                "default_restriction_id": self.restriction2.id,
            }
        )

        self.room_type_class = self.env["pms.room.type.class"].create(
            {"name": "Room Class"}
        )

        self.room_type = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.property1.id, self.property2.id],
                "name": "Single",
                "code_type": "SIN",
                "class_id": self.room_type_class.id,
                "list_price": 30,
            }
        )

        self.room = self.env["pms.room"].create(
            {
                "pms_property_id": self.property1.id,
                "name": "Single 101",
                "room_type_id": self.room_type.id,
            }
        )

        self.room2 = self.env["pms.room"].create(
            {
                "pms_property_id": self.property2.id,
                "name": "Single 102",
                "room_type_id": self.room_type.id,
            }
        )

        self.pricelist = self.env["product.pricelist"].create(
            {
                "name": "pricelist_1",
            }
        )

    @freeze_time("2000-01-01 00:00:00")
    def test_items_sort_applied_on(self):

        # ARRANGE
        self.create_common_scenario()

        self.item1 = self.env["product.pricelist.item"].create(
            {
                "name": "item_1",
                "categ_id": self.product_category.id,
                "applied_on": "2_product_category",
                "date_start": datetime.datetime.now(),
                "date_end": datetime.datetime.now() + datetime.timedelta(days=3),
                "pms_property_ids": [self.property1.id],
                "fixed_price": 40.0,
                "pricelist_id": self.pricelist.id,
                "compute_price": "fixed",
            }
        )

        self.item2 = self.env["product.pricelist.item"].create(
            {
                "name": "item_2",
                "applied_on": "0_product_variant",
                "product_id": self.room_type.product_id.id,
                "date_start": datetime.datetime.now(),
                "date_end": datetime.datetime.now() + datetime.timedelta(days=3),
                "pms_property_ids": [self.property1.id],
                "fixed_price": 50.0,
                "pricelist_id": self.pricelist.id,
                "compute_price": "fixed",
            }
        )

        reservation = self.env["pms.reservation"].create(
            {
                "checkin": datetime.datetime.today(),
                "checkout": datetime.datetime.today() + datetime.timedelta(days=3),
                "preferred_room_id": self.room.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
            }
        )

        # ACT
        n_days = (reservation.checkout - reservation.checkin).days
        expected_price = self.item2.fixed_price * n_days

        # ASSERT
        self.assertEqual(
            expected_price, reservation.price_total, "The price is not as expected"
        )

    @freeze_time("2000-01-16 00:00:00")
    def test_items_sort_date(self):

        # ARRANGE
        self.create_common_scenario()

        self.item1 = self.env["product.pricelist.item"].create(
            {
                "name": "item_1",
                "applied_on": "0_product_variant",
                "product_id": self.room_type.product_id.id,
                "date_start": datetime.datetime.today() + datetime.timedelta(days=3),
                "date_end": datetime.datetime.today()
                + datetime.timedelta(days=5, hours=23, minutes=59),
                "fixed_price": 40.0,
                "pricelist_id": self.pricelist.id,
                "compute_price": "fixed",
            }
        )

        self.item2 = self.env["product.pricelist.item"].create(
            {
                "name": "item_2",
                "applied_on": "0_product_variant",
                "product_id": self.room_type.product_id.id,
                "date_start": datetime.datetime.today(),
                "date_end": datetime.datetime.today()
                + datetime.timedelta(days=10, hours=23, minutes=59),
                "fixed_price": 50.0,
                "pricelist_id": self.pricelist.id,
                "compute_price": "fixed",
            }
        )

        reservation = self.env["pms.reservation"].create(
            {
                "checkin": datetime.datetime.today()
                + datetime.timedelta(days=3, hours=12, minutes=00),
                "checkout": datetime.datetime.today()
                + datetime.timedelta(days=5, hours=12, minutes=00),
                "preferred_room_id": self.room.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
            }
        )
        # ACT
        n_days = (reservation.checkout - reservation.checkin).days
        expected_price = self.item1.fixed_price * n_days
        # ASSERT
        self.assertEqual(
            expected_price, reservation.price_total, "The price is not as expected"
        )

    @freeze_time("2000-01-05 00:00:00")
    def test_items_sort_property(self):

        # ARRANGE
        self.create_common_scenario()

        self.item1 = self.env["product.pricelist.item"].create(
            {
                "name": "item_1",
                "applied_on": "0_product_variant",
                "product_id": self.room_type.product_id.id,
                "date_start": datetime.datetime.today(),
                "date_end": datetime.datetime.today()
                + datetime.timedelta(days=5, hours=23, minutes=59),
                "fixed_price": 40.0,
                "pricelist_id": self.pricelist.id,
                "compute_price": "fixed",
            }
        )

        self.item2 = self.env["product.pricelist.item"].create(
            {
                "name": "item_2",
                "applied_on": "0_product_variant",
                "product_id": self.room_type.product_id.id,
                "date_start": datetime.datetime.today(),
                "date_end": datetime.datetime.today()
                + datetime.timedelta(days=5, hours=23, minutes=59),
                "fixed_price": 50.0,
                "pms_property_ids": [self.property1.id],
                "pricelist_id": self.pricelist.id,
                "compute_price": "fixed",
            }
        )

        reservation = self.env["pms.reservation"].create(
            {
                "checkin": datetime.datetime.today()
                + datetime.timedelta(days=2, hours=12, minutes=00),
                "checkout": datetime.datetime.today()
                + datetime.timedelta(days=5, hours=12, minutes=00),
                "preferred_room_id": self.room.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
            }
        )
        # ACT
        n_days = (reservation.checkout - reservation.checkin).days
        expected_price = self.item2.fixed_price * n_days
        # ASSERT
        self.assertEqual(
            expected_price, reservation.price_total, "The price is not as expected"
        )

    @freeze_time("2000-01-20 00:00:00")
    def test_three_items_sort_applied_on(self):

        # ARRANGE
        self.create_common_scenario()

        self.item1 = self.env["product.pricelist.item"].create(
            {
                "name": "item_1",
                "applied_on": "0_product_variant",
                "product_id": self.room_type.product_id.id,
                "date_start": datetime.datetime.today(),
                "date_end": datetime.datetime.today()
                + datetime.timedelta(days=1, hours=23, minutes=59),
                "fixed_price": 40.0,
                "pricelist_id": self.pricelist.id,
                "compute_price": "fixed",
            }
        )

        self.item2 = self.env["product.pricelist.item"].create(
            {
                "name": "item_2",
                "product_id": self.room_type.product_id.id,
                "product_tmpl_id": self.product_template.id,
                "applied_on": "1_product",
                "date_start": datetime.datetime.today(),
                "date_end": datetime.datetime.today()
                + datetime.timedelta(days=1, hours=23, minutes=59),
                "fixed_price": 50.0,
                "pricelist_id": self.pricelist.id,
                "compute_price": "fixed",
            }
        )

        self.item3 = self.env["product.pricelist.item"].create(
            {
                "name": "item_3",
                "categ_id": self.product_category.id,
                "applied_on": "2_product_category",
                "product_id": self.room_type.product_id.id,
                "date_start": datetime.datetime.today(),
                "date_end": datetime.datetime.today()
                + datetime.timedelta(days=1, hours=23, minutes=59),
                "fixed_price": 60.0,
                "pricelist_id": self.pricelist.id,
                "compute_price": "fixed",
            }
        )

        reservation = self.env["pms.reservation"].create(
            {
                "checkin": datetime.datetime.today()
                + datetime.timedelta(hours=12, minutes=00),
                "checkout": datetime.datetime.today()
                + datetime.timedelta(days=1, hours=12, minutes=00),
                "preferred_room_id": self.room.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
            }
        )
        # ACT
        expected_price = self.item1.fixed_price
        # ASSERT
        self.assertEqual(
            expected_price, reservation.price_total, "The price is not as expected"
        )

    @freeze_time("2000-01-25 00:00:00")
    def test_three_items_sort_date(self):

        # ARRANGE
        self.create_common_scenario()

        self.item1 = self.env["product.pricelist.item"].create(
            {
                "name": "item_1",
                "applied_on": "0_product_variant",
                "product_id": self.room_type.product_id.id,
                "date_start": datetime.datetime.today(),
                "date_end": datetime.datetime.today()
                + datetime.timedelta(days=6, hours=23, minutes=59),
                "fixed_price": 40.0,
                "pricelist_id": self.pricelist.id,
                "compute_price": "fixed",
            }
        )

        self.item2 = self.env["product.pricelist.item"].create(
            {
                "name": "item_2",
                "applied_on": "0_product_variant",
                "product_id": self.room_type.product_id.id,
                "date_start": datetime.datetime.today()
                + datetime.timedelta(days=1, hours=00, minutes=00),
                "date_end": datetime.datetime.today()
                + datetime.timedelta(days=5, hours=23, minutes=59),
                "fixed_price": 50.0,
                "pricelist_id": self.pricelist.id,
                "compute_price": "fixed",
            }
        )

        self.item3 = self.env["product.pricelist.item"].create(
            {
                "name": "item_3",
                "applied_on": "0_product_variant",
                "product_id": self.room_type.product_id.id,
                "date_start": datetime.datetime.today()
                + datetime.timedelta(days=2, hours=00, minutes=00),
                "date_end": datetime.datetime.today()
                + datetime.timedelta(days=4, hours=23, minutes=59),
                "fixed_price": 60.0,
                "pricelist_id": self.pricelist.id,
                "compute_price": "fixed",
            }
        )

        reservation = self.env["pms.reservation"].create(
            {
                "checkin": datetime.datetime.today()
                + datetime.timedelta(days=3, hours=10, minutes=00),
                "checkout": datetime.datetime.today()
                + datetime.timedelta(days=4, hours=12, minutes=00),
                "preferred_room_id": self.room.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
            }
        )
        # ACT
        expected_price = self.item3.fixed_price
        # ASSERT
        self.assertEqual(
            expected_price, reservation.price_total, "The price is not as expected"
        )

    @freeze_time("2000-02-01 00:00:00")
    def test_three_items_sort_property(self):

        # ARRANGE
        self.create_common_scenario()

        self.item1 = self.env["product.pricelist.item"].create(
            {
                "name": "item_1",
                "applied_on": "0_product_variant",
                "product_id": self.room_type.product_id.id,
                "date_start": datetime.datetime.today(),
                "date_end": datetime.datetime.today()
                + datetime.timedelta(days=3, hours=23, minutes=59),
                "fixed_price": 40.0,
                "pricelist_id": self.pricelist.id,
                "compute_price": "fixed",
            }
        )

        self.item2 = self.env["product.pricelist.item"].create(
            {
                "name": "item_2",
                "applied_on": "0_product_variant",
                "product_id": self.room_type.product_id.id,
                "date_start": datetime.datetime.today(),
                "date_end": datetime.datetime.today()
                + datetime.timedelta(days=3, hours=23, minutes=59),
                "fixed_price": 50.0,
                "pms_property_ids": [self.property1.id],
                "pricelist_id": self.pricelist.id,
                "compute_price": "fixed",
            }
        )

        self.item3 = self.env["product.pricelist.item"].create(
            {
                "name": "item_3",
                "applied_on": "0_product_variant",
                "product_id": self.room_type.product_id.id,
                "date_start": datetime.datetime.today(),
                "date_end": datetime.datetime.today()
                + datetime.timedelta(days=3, hours=23, minutes=59),
                "fixed_price": 60.0,
                "pms_property_ids": [self.property1.id, self.property2.id],
                "pricelist_id": self.pricelist.id,
                "compute_price": "fixed",
            }
        )

        reservation = self.env["pms.reservation"].create(
            {
                "checkin": datetime.datetime.today(),
                "checkout": datetime.datetime.today()
                + datetime.timedelta(days=2, hours=12, minutes=00),
                "preferred_room_id": self.room.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
            }
        )
        # ACT
        n_days = (reservation.checkout - reservation.checkin).days
        expected_price = self.item3.fixed_price * n_days
        # ASSERT
        self.assertEqual(
            expected_price, reservation.price_total, "The price is not as expected"
        )

    @freeze_time("2000-02-01 00:00:00")
    def test_sort_applied_on_before_date(self):
        # ARRANGE
        self.create_common_scenario()

        self.item1 = self.env["product.pricelist.item"].create(
            {
                "name": "item_1",
                "applied_on": "0_product_variant",
                "product_id": self.room_type.product_id.id,
                "date_start": datetime.datetime.today(),
                "date_end": datetime.datetime.today()
                + datetime.timedelta(days=8, hours=23, minutes=59),
                "fixed_price": 40.0,
                "pricelist_id": self.pricelist.id,
                "compute_price": "fixed",
            }
        )

        self.item2 = self.env["product.pricelist.item"].create(
            {
                "name": "item_2",
                "product_id": self.room_type.product_id.id,
                "product_tmpl_id": self.product_template.id,
                "applied_on": "1_product",
                "date_start": datetime.datetime.today()
                + datetime.timedelta(days=2, hours=00, minutes=00),
                "date_end": datetime.datetime.today()
                + datetime.timedelta(days=5, hours=23, minutes=59),
                "fixed_price": 50.0,
                "pms_property_ids": [self.property1.id],
                "pricelist_id": self.pricelist.id,
                "compute_price": "fixed",
            }
        )

        reservation = self.env["pms.reservation"].create(
            {
                "checkin": datetime.datetime.today()
                + datetime.timedelta(days=2, hours=12, minutes=00),
                "checkout": datetime.datetime.today()
                + datetime.timedelta(days=4, hours=12, minutes=00),
                "preferred_room_id": self.room.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
            }
        )
        # ACT
        n_days = (reservation.checkout - reservation.checkin).days
        expected_price = self.item1.fixed_price * n_days
        # ASSERT
        self.assertEqual(
            expected_price, reservation.price_total, "The price is not as expected"
        )

    @freeze_time("2000-02-10 00:00:00")
    def test_sort_date_before_property(self):
        # ARRANGE
        self.create_common_scenario()

        self.item1 = self.env["product.pricelist.item"].create(
            {
                "name": "item_1",
                "applied_on": "0_product_variant",
                "product_id": self.room_type.product_id.id,
                "date_start": datetime.datetime.today(),
                "date_end": datetime.datetime.today()
                + datetime.timedelta(days=10, hours=23, minutes=59),
                "fixed_price": 40.0,
                "pms_property_ids": [self.property1.id],
                "pricelist_id": self.pricelist.id,
                "compute_price": "fixed",
            }
        )

        self.item2 = self.env["product.pricelist.item"].create(
            {
                "name": "item_2",
                "applied_on": "0_product_variant",
                "product_id": self.room_type.product_id.id,
                "date_start": datetime.datetime.today()
                + datetime.timedelta(days=2, hours=00, minutes=00),
                "date_end": datetime.datetime.today()
                + datetime.timedelta(days=5, hours=23, minutes=59),
                "fixed_price": 50.0,
                "pricelist_id": self.pricelist.id,
                "compute_price": "fixed",
            }
        )

        reservation = self.env["pms.reservation"].create(
            {
                "checkin": datetime.datetime.today()
                + datetime.timedelta(days=2, hours=12, minutes=00),
                "checkout": datetime.datetime.today()
                + datetime.timedelta(days=4, hours=12, minutes=00),
                "preferred_room_id": self.room.id,
                "pms_property_id": self.property1.id,
                "pricelist_id": self.pricelist.id,
            }
        )
        # ACT
        n_days = (reservation.checkout - reservation.checkin).days
        expected_price = self.item2.fixed_price * n_days
        # ASSERT
        self.assertEqual(
            expected_price, reservation.price_total, "The price is not as expected"
        )
