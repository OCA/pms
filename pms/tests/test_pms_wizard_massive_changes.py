import datetime

from freezegun import freeze_time

from odoo import fields
from odoo.tests import common


class TestPmsWizardMassiveChanges(common.SavepointCase):
    def create_common_scenario(self):
        # product.pricelist
        self.test_pricelist = self.env["product.pricelist"].create(
            {
                "name": "test pricelist 1",
            }
        )
        # pms.availability.plan
        self.test_availability_plan = self.env["pms.availability.plan"].create(
            {
                "name": "Availability plan for TEST",
                "pms_pricelist_ids": [(6, 0, [self.test_pricelist.id])],
            }
        )
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
        # pms.property
        self.test_property = self.env["pms.property"].create(
            {
                "name": "MY PMS TEST",
                "company_id": self.env.ref("base.main_company").id,
                "default_pricelist_id": self.test_pricelist.id,
                "folio_sequence_id": self.folio_sequence.id,
                "reservation_sequence_id": self.reservation_sequence.id,
                "checkin_sequence_id": self.checkin_sequence.id,
            }
        )
        # pms.room.type.class
        self.test_room_type_class = self.env["pms.room.type.class"].create(
            {"name": "Room", "default_code": "ROOM"}
        )

        # pms.room.type
        self.test_room_type_single = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.test_property.id],
                "name": "Single Test",
                "default_code": "SNG_Test",
                "class_id": self.test_room_type_class.id,
            }
        )
        # pms.room.type
        self.test_room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.test_property.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.test_room_type_class.id,
            }
        )

    # MASSIVE CHANGE WIZARD TESTS ON AVAILABILITY RULES

    @freeze_time("1980-12-01")
    def test_num_availability_rules_create(self):

        # TEST CASE
        # rules should be created consistently for 1,2,3,4 days

        # ARRANGE
        self.create_common_scenario()

        for days in [0, 1, 2, 3]:
            with self.subTest(k=days):
                num_exp_rules_to_create = days + 1

                self.env["pms.massive.changes.wizard"].create(
                    {
                        "massive_changes_on": "availability_plan",
                        "availability_plan_id": self.test_availability_plan.id,
                        "start_date": fields.date.today(),
                        "end_date": fields.date.today() + datetime.timedelta(days=days),
                        "room_type_id": self.test_room_type_double.id,
                        "pms_property_ids": [self.test_property.id],
                    }
                ).apply_massive_changes()

                self.assertEqual(
                    len(self.test_availability_plan.rule_ids),
                    num_exp_rules_to_create,
                    "the number of rules created by should contains all the "
                    "days between start and finish (both included)",
                )

    @freeze_time("1980-12-01")
    def test_num_availability_rules_create_no_room_type(self):
        # TEST CASE
        # (days x room_types) rules should be created

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today()
        date_to = fields.date.today() + datetime.timedelta(days=3)

        num_room_types = self.env["pms.room.type"].search_count(
            [
                "|",
                ("pms_property_ids", "=", False),
                ("pms_property_ids", "in", self.test_property.id),
            ]
        )
        num_exp_rules_to_create = ((date_to - date_from).days + 1) * num_room_types

        # ACT
        self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "availability_plan",
                "availability_plan_id": self.test_availability_plan.id,
                "start_date": date_from,
                "end_date": date_to,
                "pms_property_ids": [self.test_property.id],
            }
        ).apply_massive_changes()

        # ASSERT
        self.assertEqual(
            len(self.test_availability_plan.rule_ids),
            num_exp_rules_to_create,
            "the number of rules created by the wizard should consider all "
            "room types",
        )

    @freeze_time("1980-12-01")
    def test_value_availability_rules_create(self):
        # TEST CASE
        # Rule values should be set correctly

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today()
        date_to = fields.date.today()

        vals = {
            "massive_changes_on": "availability_plan",
            "availability_plan_id": self.test_availability_plan.id,
            "start_date": date_from,
            "end_date": date_to,
            "room_type_id": self.test_room_type_double.id,
            "quota": 50,
            "max_avail": 5,
            "min_stay": 10,
            "min_stay_arrival": 10,
            "max_stay": 10,
            "max_stay_arrival": 10,
            "closed": True,
            "closed_arrival": True,
            "closed_departure": True,
            "pms_property_ids": [self.test_property.id],
        }

        # ACT
        self.env["pms.massive.changes.wizard"].create(vals).apply_massive_changes()

        # ASSERT
        del vals["massive_changes_on"]
        del vals["availability_plan_id"]
        del vals["start_date"]
        del vals["end_date"]
        del vals["room_type_id"]
        del vals["pms_property_ids"]
        for key in vals:
            with self.subTest(k=key):
                self.assertEqual(
                    self.test_availability_plan.rule_ids[0][key],
                    vals[key],
                    "The value of " + key + " is not correctly established",
                )

    @freeze_time("1980-12-01")
    def test_day_of_week_availability_rules_create(self):
        # TEST CASE
        # rules for each day of week should be created

        # ARRANGE
        self.create_common_scenario()
        test_case_week_days = [
            [1, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 1],
        ]

        date_from = fields.date.today()
        date_to = fields.date.today() + datetime.timedelta(days=6)

        wizard = self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "availability_plan",
                "availability_plan_id": self.test_availability_plan.id,
                "room_type_id": self.test_room_type_double.id,
                "start_date": date_from,
                "end_date": date_to,
                "pms_property_ids": [self.test_property.id],
            }
        )

        for index, test_case in enumerate(test_case_week_days):
            with self.subTest(k=test_case):
                # ARRANGE
                wizard.write(
                    {
                        "apply_on_monday": test_case[0],
                        "apply_on_tuesday": test_case[1],
                        "apply_on_wednesday": test_case[2],
                        "apply_on_thursday": test_case[3],
                        "apply_on_friday": test_case[4],
                        "apply_on_saturday": test_case[5],
                        "apply_on_sunday": test_case[6],
                    }
                )
                # ACT
                wizard.apply_massive_changes()
                availability_rules = self.test_availability_plan.rule_ids.sorted(
                    key=lambda s: s.date
                )
                # ASSERT
                self.assertTrue(
                    availability_rules[index].date.timetuple()[6] == index
                    and test_case[index],
                    "Rule not created on correct day of week",
                )

    @freeze_time("1980-12-01")
    def test_no_overwrite_values_not_setted(self):
        # TEST CASE
        # A rule value shouldnt overwrite with the default values
        # another rules for the same day and room type

        # ARRANGE
        self.create_common_scenario()
        date = fields.date.today()
        initial_quota = 20
        self.env["pms.availability.plan.rule"].create(
            {
                "availability_plan_id": self.test_availability_plan.id,
                "room_type_id": self.test_room_type_double.id,
                "date": date,
                "quota": initial_quota,
                "pms_property_id": self.test_property.id,
            }
        )
        vals_wizard = {
            "massive_changes_on": "availability_plan",
            "availability_plan_id": self.test_availability_plan.id,
            "start_date": date,
            "end_date": date,
            "room_type_id": self.test_room_type_double.id,
            "apply_max_avail": True,
            "max_avail": 2,
            "pms_property_ids": [self.test_property.id],
        }

        # ACT
        self.env["pms.massive.changes.wizard"].create(
            vals_wizard
        ).apply_massive_changes()

        # ASSERT
        self.assertEqual(
            self.test_availability_plan.rule_ids[0].quota,
            initial_quota,
            "A rule value shouldnt overwrite with the default values "
            "another rules for the same day and room type",
        )

    # MASSIVE CHANGE WIZARD TESTS ON PRICELIST ITEMS

    @freeze_time("1980-12-01")
    def test_pricelist_items_create(self):
        # TEST CASE
        # items should be created consistently for 1,2,3,4 days

        # ARRANGE
        self.create_common_scenario()
        for days in [0, 1, 2, 3]:
            with self.subTest(k=days):

                # ARRANGE
                num_exp_items_to_create = days + 1
                self.test_pricelist.item_ids = False

                # ACT
                self.env["pms.massive.changes.wizard"].create(
                    {
                        "massive_changes_on": "pricelist",
                        "pricelist_id": self.test_pricelist.id,
                        "start_date": fields.date.today(),
                        "end_date": fields.date.today() + datetime.timedelta(days=days),
                        "room_type_id": self.test_room_type_double.id,
                        "pms_property_ids": [self.test_property.id],
                    }
                ).apply_massive_changes()
                # ASSERT
                self.assertEqual(
                    len(
                        self.test_pricelist.item_ids
                        if self.test_pricelist.item_ids
                        else []
                    ),
                    num_exp_items_to_create,
                    "the number of rules created by the wizard should include all the "
                    "days between start and finish (both included)",
                )

    @freeze_time("1980-12-01")
    def test_num_pricelist_items_create_no_room_type(self):
        # TEST CASE
        # (days x room_types) items should be created

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today()
        date_to = fields.date.today() + datetime.timedelta(days=3)
        num_room_types = self.env["pms.room.type"].search_count(
            [
                "|",
                ("pms_property_ids", "=", False),
                ("pms_property_ids", "in", self.test_property.id),
            ]
        )
        num_exp_items_to_create = ((date_to - date_from).days + 1) * num_room_types

        # ACT
        self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "pricelist",
                "pricelist_id": self.test_pricelist.id,
                "start_date": date_from,
                "end_date": date_to,
                "pms_property_ids": [self.test_property.id],
            }
        ).apply_massive_changes()

        # ASSERT
        self.assertEqual(
            len(self.test_pricelist.item_ids),
            num_exp_items_to_create,
            "the number of rules created by the wizard should consider all "
            "room types when one is not applied",
        )

    @freeze_time("1980-12-01")
    def test_value_pricelist_items_create(self):
        # TEST CASE
        # Item values should be set correctly

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today()
        date_to = fields.date.today()

        price = 20
        min_quantity = 3

        vals = {
            "pricelist_id": self.test_pricelist,
            "date_start": date_from,
            "date_end": date_to,
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": self.test_room_type_double.product_id,
            "fixed_price": price,
            "min_quantity": min_quantity,
        }

        # ACT
        self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "pricelist",
                "pricelist_id": self.test_pricelist.id,
                "start_date": date_from,
                "end_date": date_to,
                "room_type_id": self.test_room_type_double.id,
                "price": price,
                "min_quantity": min_quantity,
                "pms_property_ids": [self.test_property.id],
            }
        ).apply_massive_changes()
        vals["date_start_overnight"] = date_from
        vals["date_end_overnight"] = date_to

        del vals["date_start"]
        del vals["date_end"]

        # ASSERT
        for key in vals:
            with self.subTest(k=key):
                self.assertEqual(
                    self.test_pricelist.item_ids[0][key],
                    vals[key],
                    "The value of " + key + " is not correctly established",
                )

    @freeze_time("1980-12-01")
    def test_day_of_week_pricelist_items_create(self):
        # TEST CASE
        # items for each day of week should be created
        # ARRANGE
        self.create_common_scenario()
        test_case_week_days = [
            [1, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 1],
        ]
        date_from = fields.date.today()
        date_to = date_from + datetime.timedelta(days=6)
        wizard = self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "pricelist",
                "pricelist_id": self.test_pricelist.id,
                "room_type_id": self.test_room_type_double.id,
                "start_date": date_from,
                "end_date": date_to,
                "pms_property_ids": [self.test_property.id],
            }
        )
        for index, test_case in enumerate(test_case_week_days):
            with self.subTest(k=test_case):
                # ARRANGE
                wizard.write(
                    {
                        "apply_on_monday": test_case[0],
                        "apply_on_tuesday": test_case[1],
                        "apply_on_wednesday": test_case[2],
                        "apply_on_thursday": test_case[3],
                        "apply_on_friday": test_case[4],
                        "apply_on_saturday": test_case[5],
                        "apply_on_sunday": test_case[6],
                    }
                )
                self.test_pricelist.item_ids = False

                # ACT
                wizard.apply_massive_changes()

                # ASSERT
                pricelist_items = self.test_pricelist.item_ids.sorted(
                    key=lambda s: s.date_start_overnight
                )

                # ASSERT
                self.assertTrue(
                    pricelist_items[index].date_start_overnight.timetuple()[6] == index
                    and test_case[index],
                    "Rule not created on correct day of week",
                )
