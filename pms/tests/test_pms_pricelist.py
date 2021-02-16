import datetime

from odoo.exceptions import ValidationError
from odoo.tests import common, tagged


@tagged("standard", "nice")
class TestPmsPricelist(common.TransactionCase):
    def create_common_scenario(self):
        self.property1 = self.env["pms.property"].create(
            {
                "name": "Property_1",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
            }
        )

        self.property2 = self.env["pms.property"].create(
            {
                "name": "Property_2",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
            }
        )

        self.property3 = self.env["pms.property"].create(
            {
                "name": "Property_3",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.env.ref("product.list0").id,
            }
        )
        self.room_type_class = self.env["pms.room.type.class"].create(
            {"name": "Room Class", "code_class": "ROOM"}
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
        with self.assertRaises(ValidationError):
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
        with self.assertRaises(ValidationError):
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
        with self.assertRaises(ValidationError):
            Pricelist.create(
                {
                    "name": "Pricelist Test",
                    "pms_property_ids": [self.property1.id, self.property2.id],
                    "cancelation_rule_id": self.cancelation_rule.id,
                }
            )
