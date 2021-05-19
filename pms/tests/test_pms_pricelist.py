import datetime

from freezegun import freeze_time

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

        self.pricelist = self.env["product.pricelist"].create(
            {
                "name": "pricelist_1",
                "pms_property_ids": [self.property1.id, self.property2.id],
            }
        )

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

    @freeze_time("2000-01-01")
    def test_pricelist_daily_failed(self):
        self.create_common_scenario()
        test_cases = [
            {
                "compute_price": "fixed",
                "pms_property_ids": [self.property1.id, self.property2.id],
                "date_start_overnight": datetime.datetime.now(),
                "date_end_overnight": datetime.datetime.today()
                + datetime.timedelta(days=1),
            },
            {
                "compute_price": "fixed",
                "pms_property_ids": False,
                "date_start_overnight": datetime.datetime.now(),
                "date_end_overnight": datetime.datetime.today()
                + datetime.timedelta(days=1),
            },
            {
                "compute_price": "percentage",
                "pms_property_ids": [self.property1.id],
                "date_start_overnight": datetime.datetime.now(),
                "date_end_overnight": datetime.datetime.today()
                + datetime.timedelta(days=1),
            },
            {
                "compute_price": "percentage",
                "pms_property_ids": [self.property1.id, self.property2.id],
                "date_start_overnight": datetime.datetime.now(),
                "date_end_overnight": datetime.datetime.today()
                + datetime.timedelta(days=1),
            },
            {
                "compute_price": "percentage",
                "pms_property_ids": False,
                "date_start_overnight": datetime.datetime.now(),
                "date_end_overnight": datetime.datetime.today()
                + datetime.timedelta(days=1),
            },
            {
                "compute_price": "fixed",
                "pms_property_ids": [self.property1.id],
                "date_start_overnight": datetime.datetime.now(),
                "date_end_overnight": datetime.datetime.today()
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
                            "date_start_overnight": tc["date_start_overnight"],
                            "date_end_overnight": tc["date_end_overnight"],
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
                "date_start_overnight": datetime.datetime.now(),
                "date_end_overnight": datetime.datetime.today()
                + datetime.timedelta(days=1),
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
