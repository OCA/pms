import datetime

from freezegun import freeze_time

from odoo import fields

from .common import TestPms


class TestPmsWizardMassiveChanges(TestPms):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.availability_plan1 = cls.env["pms.availability.plan"].create(
            {
                "name": "Availability plan for TEST",
                "pms_pricelist_ids": [(6, 0, [cls.pricelist1.id])],
            }
        )

    # MASSIVE CHANGE WIZARD TESTS ON AVAILABILITY RULES

    def test_num_availability_rules_create(self):
        """
        Rules should be created consistently for 1,2,3,4 days
        subtests: {1 day -> 1 rule, n days -> n rules}
        """
        # ARRANGE
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        for days in [0, 1, 2, 3]:
            with self.subTest(k=days):
                num_exp_rules_to_create = days + 1
                # ACT
                self.env["pms.massive.changes.wizard"].create(
                    {
                        "massive_changes_on": "availability_plan",
                        "availability_plan_ids": [(6, 0, [self.availability_plan1.id])],
                        "start_date": fields.date.today(),
                        "end_date": fields.date.today() + datetime.timedelta(days=days),
                        "room_type_ids": [(6, 0, [room_type_double.id])],
                        "pms_property_ids": [self.pms_property1.id],
                    }
                ).apply_massive_changes()
                # ASSERT
                self.assertEqual(
                    len(self.availability_plan1.rule_ids),
                    num_exp_rules_to_create,
                    "the number of rules created should contains all the "
                    "days between start and finish (both included)",
                )

    def test_num_availability_rules_create_no_room_type(self):
        """
        Rules should be created consistently for all rooms & days.
        (days * num rooom types)
        Create rules for 4 days and for all room types.
        """
        # ARRANGE
        date_from = fields.date.today()
        date_to = fields.date.today() + datetime.timedelta(days=3)

        num_room_types = self.env["pms.room.type"].search_count(
            [
                "|",
                ("pms_property_ids", "=", False),
                ("pms_property_ids", "in", self.pms_property1.id),
            ]
        )
        num_exp_rules_to_create = ((date_to - date_from).days + 1) * num_room_types

        # ACT
        self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "availability_plan",
                "availability_plan_ids": [(6, 0, [self.availability_plan1.id])],
                "start_date": date_from,
                "end_date": date_to,
                "pms_property_ids": [self.pms_property1.id],
            }
        ).apply_massive_changes()

        # ASSERT
        self.assertEqual(
            len(self.availability_plan1.rule_ids),
            num_exp_rules_to_create,
            "the number of rules created by the wizard should consider all "
            "room types",
        )

    def test_value_availability_rules_create(self):
        """
        The value of the rules created is setted properly.
        """
        # ARRANGE
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        date_from = fields.date.today()
        date_to = fields.date.today()
        vals = {
            "massive_changes_on": "availability_plan",
            "availability_plan_ids": [(6, 0, [self.availability_plan1.id])],
            "start_date": date_from,
            "end_date": date_to,
            "room_type_ids": [(6, 0, [room_type_double.id])],
            "quota": 50,
            "max_avail": 5,
            "min_stay": 10,
            "min_stay_arrival": 10,
            "max_stay": 10,
            "max_stay_arrival": 10,
            "closed": True,
            "closed_arrival": True,
            "closed_departure": True,
            "pms_property_ids": [self.pms_property1.id],
        }
        # ACT
        self.env["pms.massive.changes.wizard"].create(vals).apply_massive_changes()
        # ASSERT
        del vals["massive_changes_on"]
        del vals["availability_plan_ids"]
        del vals["start_date"]
        del vals["end_date"]
        del vals["room_type_ids"]
        del vals["pms_property_ids"]
        for key in vals:
            with self.subTest(k=key):
                self.assertEqual(
                    self.availability_plan1.rule_ids[0][key],
                    vals[key],
                    "The value of " + key + " is not correctly established",
                )

    @freeze_time("1980-12-01")
    def test_day_of_week_availability_rules_create(self):
        """
        Rules for each day of week should be created.
        """
        # ARRANGE
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
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
                "availability_plan_ids": [(6, 0, [self.availability_plan1.id])],
                "room_type_ids": [(6, 0, [room_type_double.id])],
                "start_date": date_from,
                "end_date": date_to,
                "pms_property_ids": [self.pms_property1.id],
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
                availability_rules = self.availability_plan1.rule_ids.sorted(
                    key=lambda s: s.date
                )
                # ASSERT
                self.assertTrue(
                    availability_rules[index].date.timetuple()[6] == index
                    and test_case[index],
                    "Rule not created on correct day of week.",
                )

    def test_no_overwrite_values_not_setted(self):
        """
        A rule value shouldnt overwrite with the default values
        another rules for the same day and room type.
        Create a rule with quota and another rule for the same date with max
        avail. Should not overwrite quota.
        """
        # ARRANGE
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        date = fields.date.today()
        initial_quota = 20
        self.env["pms.availability.plan.rule"].create(
            {
                "availability_plan_id": self.availability_plan1.id,
                "room_type_id": room_type_double.id,
                "date": date,
                "quota": initial_quota,
                "pms_property_id": self.pms_property1.id,
            }
        )
        vals_wizard = {
            "massive_changes_on": "availability_plan",
            "availability_plan_ids": [(6, 0, [self.availability_plan1.id])],
            "start_date": date,
            "end_date": date,
            "room_type_ids": [(6, 0, [room_type_double.id])],
            "apply_max_avail": True,
            "max_avail": 2,
            "pms_property_ids": [self.pms_property1.id],
        }
        # ACT
        self.env["pms.massive.changes.wizard"].create(
            vals_wizard
        ).apply_massive_changes()
        # ASSERT
        self.assertEqual(
            self.availability_plan1.rule_ids[0].quota,
            initial_quota,
            "A rule value shouldnt overwrite with the default values "
            "another rules for the same day and room type",
        )

    def test_several_availability_plans(self):
        """
        If several availability plans are set, the wizard should create as
        many rules as availability plans.
        """
        # ARRANGE
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        availability_plan2 = self.env["pms.availability.plan"].create(
            {
                "name": "Second availability plan for TEST",
                "pms_pricelist_ids": [self.pricelist1.id],
            }
        )
        expected_av_plans = [
            self.availability_plan1.id,
            availability_plan2.id,
        ]
        date_from = fields.date.today()
        date_to = fields.date.today()
        vals_wizard = {
            "massive_changes_on": "availability_plan",
            "availability_plan_ids": [
                (
                    6,
                    0,
                    [
                        self.availability_plan1.id,
                        availability_plan2.id,
                    ],
                )
            ],
            "room_type_ids": [(6, 0, [room_type_double.id])],
            "pms_property_ids": [self.pms_property1.id],
            "start_date": date_from,
            "end_date": date_to,
        }
        # ACT
        self.env["pms.massive.changes.wizard"].create(
            vals_wizard
        ).apply_massive_changes()
        # ASSERT
        self.assertEqual(
            set(expected_av_plans),
            set(
                self.env["pms.availability.plan.rule"]
                .search([("room_type_id", "=", room_type_double.id)])
                .mapped("availability_plan_id")
                .ids
            ),
            "The wizard should create as many rules as availability plans given.",
        )

    def test_several_room_types_availability_plan(self):
        """
        If several room types are set, the wizard should create as
        many rules as room types.
        """
        # ARRANGE
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        room_type_single = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Single Test",
                "default_code": "SNG_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        expected_room_types = [
            room_type_double.id,
            room_type_single.id,
        ]
        date_from = fields.date.today()
        date_to = fields.date.today()
        vals_wizard = {
            "massive_changes_on": "availability_plan",
            "availability_plan_ids": [(6, 0, [self.availability_plan1.id])],
            "room_type_ids": [
                (
                    6,
                    0,
                    [room_type_double.id, room_type_single.id],
                )
            ],
            "pms_property_ids": [self.pms_property1.id],
            "start_date": date_from,
            "end_date": date_to,
        }
        # ACT
        self.env["pms.massive.changes.wizard"].create(
            vals_wizard
        ).apply_massive_changes()
        # ASSERT
        self.assertEqual(
            set(expected_room_types),
            set(
                self.env["pms.availability.plan.rule"]
                .search([("availability_plan_id", "=", self.availability_plan1.id)])
                .mapped("room_type_id")
                .ids
            ),
            "The wizard should create as many rules as room types given.",
        )

    def test_several_properties_availability_plan(self):
        """
        If several properties are set, the wizard should create as
        many rules as properties.
        """
        # ARRANGE
        pms_property2 = self.env["pms.property"].create(
            {
                "name": "MY 2nd PMS TEST",
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        room_type_double.pms_property_ids = [
            (6, 0, [self.pms_property1.id, pms_property2.id])
        ]
        expected_properties = [
            self.pms_property1.id,
            pms_property2.id,
        ]
        date_from = fields.date.today()
        date_to = fields.date.today()
        vals_wizard = {
            "massive_changes_on": "availability_plan",
            "availability_plan_ids": [(6, 0, [self.availability_plan1.id])],
            "room_type_ids": [(6, 0, [room_type_double.id])],
            "pms_property_ids": [(6, 0, [self.pms_property1.id, pms_property2.id])],
            "start_date": date_from,
            "end_date": date_to,
        }
        # ACT
        self.env["pms.massive.changes.wizard"].create(
            vals_wizard
        ).apply_massive_changes()
        # ASSERT
        self.assertEqual(
            set(expected_properties),
            set(
                self.env["pms.availability.plan.rule"]
                .search([("availability_plan_id", "=", self.availability_plan1.id)])
                .mapped("pms_property_id")
                .ids
            ),
            "The wizard should create as many rules as properties given.",
        )

    def test_create_rule_existing_previous(self):
        """
        If there's a previous rule with some value and new values are set
        that contains date of previuos value should overwrite the value.
        """
        # ARRANGE
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        date = fields.date.today()
        initial_quota = 20
        self.env["pms.availability.plan.rule"].create(
            {
                "availability_plan_id": self.availability_plan1.id,
                "room_type_id": room_type_double.id,
                "date": date,
                "quota": initial_quota,
                "pms_property_id": self.pms_property1.id,
            }
        )
        vals_wizard = {
            "massive_changes_on": "availability_plan",
            "availability_plan_ids": [(6, 0, [self.availability_plan1.id])],
            "start_date": date,
            "end_date": fields.date.today() + datetime.timedelta(days=1),
            "room_type_ids": [(6, 0, [room_type_double.id])],
            "apply_quota": True,
            "quota": 20,
            "pms_property_ids": [self.pms_property1.id],
        }

        # ACT
        self.env["pms.massive.changes.wizard"].create(
            vals_wizard
        ).apply_massive_changes()

        # ASSERT
        self.assertEqual(
            self.availability_plan1.rule_ids[0].quota,
            initial_quota,
            "A rule value shouldnt overwrite with the default values "
            "another rules for the same day and room type",
        )

    # MASSIVE CHANGE WIZARD TESTS ON PRICELIST ITEMS

    def test_pricelist_items_create(self):
        """
        Pricelist items should be created consistently for 1,2,3,4 days
        subtests: {1 day -> 1 pricelist item, n days -> n pricelist items}
        """
        # ARRANGE
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        for days in [0, 1, 2, 3]:
            with self.subTest(k=days):
                # ARRANGE
                num_exp_items_to_create = days + 1
                self.pricelist1.item_ids = False
                # ACT
                self.env["pms.massive.changes.wizard"].create(
                    {
                        "massive_changes_on": "pricelist",
                        "pricelist_ids": [(6, 0, [self.pricelist1.id])],
                        "start_date": fields.date.today(),
                        "end_date": fields.date.today() + datetime.timedelta(days=days),
                        "room_type_ids": [(6, 0, [room_type_double.id])],
                        "pms_property_ids": [self.pms_property1.id],
                    }
                ).apply_massive_changes()
                # ASSERT
                self.assertEqual(
                    len(self.pricelist1.item_ids if self.pricelist1.item_ids else []),
                    num_exp_items_to_create,
                    "the number of rules created by the wizard should include all the "
                    "days between start and finish (both included)",
                )

    def test_num_pricelist_items_create_no_room_type(self):
        """
        Pricelist items should be created consistently for all rooms & days.
        (days * num rooom types)
        Create pricelist item for 4 days and for all room types.
        """
        # ARRANGE
        date_from = fields.date.today()
        date_to = fields.date.today() + datetime.timedelta(days=3)
        num_room_types = self.env["pms.room.type"].search_count(
            [
                "|",
                ("pms_property_ids", "=", False),
                ("pms_property_ids", "in", self.pms_property1.id),
            ]
        )
        num_exp_items_to_create = ((date_to - date_from).days + 1) * num_room_types
        # ACT
        self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "pricelist",
                "pricelist_ids": [(6, 0, [self.pricelist1.id])],
                "start_date": date_from,
                "end_date": date_to,
                "pms_property_ids": [self.pms_property1.id],
            }
        ).apply_massive_changes()
        # ASSERT
        self.assertEqual(
            len(self.pricelist1.item_ids),
            num_exp_items_to_create,
            "the number of rules created by the wizard should consider all "
            "room types when one is not applied",
        )

    def test_value_pricelist_items_create(self):
        """
        The value of the rules created is setted properly.
        """
        # ARRANGE
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        date_from = fields.date.today()
        date_to = fields.date.today()
        price = 20
        min_quantity = 3
        vals = {
            "pricelist_id": self.pricelist1,
            "date_start": date_from,
            "date_end": date_to,
            "compute_price": "fixed",
            "applied_on": "0_product_variant",
            "product_id": room_type_double.product_id,
            "fixed_price": price,
            "min_quantity": min_quantity,
        }
        # ACT
        self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "pricelist",
                "pricelist_ids": [(6, 0, [self.pricelist1.id])],
                "start_date": date_from,
                "end_date": date_to,
                "room_type_ids": [(6, 0, [room_type_double.id])],
                "price": price,
                "min_quantity": min_quantity,
                "pms_property_ids": [self.pms_property1.id],
            }
        ).apply_massive_changes()
        vals["date_start_consumption"] = date_from
        vals["date_end_consumption"] = date_to
        del vals["date_start"]
        del vals["date_end"]
        # ASSERT
        for key in vals:
            with self.subTest(k=key):
                self.assertEqual(
                    self.pricelist1.item_ids[0][key],
                    vals[key],
                    "The value of " + key + " is not correctly established",
                )

    @freeze_time("1980-12-01")
    def test_day_of_week_pricelist_items_create(self):
        """
        Pricelist items for each day of week should be created.
        """
        # ARRANGE
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
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
                "pricelist_ids": [(6, 0, [self.pricelist1.id])],
                "room_type_ids": [(6, 0, [room_type_double.id])],
                "start_date": date_from,
                "end_date": date_to,
                "pms_property_ids": [self.pms_property1.id],
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
                self.pricelist1.item_ids = False
                # ACT
                wizard.apply_massive_changes()
                pricelist_items = self.pricelist1.item_ids.sorted(
                    key=lambda s: s.date_start_consumption
                )
                # ASSERT
                self.assertTrue(
                    pricelist_items[index].date_start_consumption.timetuple()[6]
                    == index
                    and test_case[index],
                    "Rule not created on correct day of week",
                )

    def test_several_pricelists(self):
        """
        If several pricelist are set, the wizard should create as
        many pricelist items as pricelists.
        """
        # ARRANGE
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        pricelist2 = self.env["product.pricelist"].create(
            {
                "name": "test pricelist 2",
                "availability_plan_id": self.availability_plan1.id,
                "is_pms_available": True,
            }
        )
        expected_pricelists = [self.pricelist1.id, pricelist2.id]
        date_from = fields.date.today()
        date_to = fields.date.today()
        vals_wizard = {
            "massive_changes_on": "pricelist",
            "pricelist_ids": [(6, 0, [self.pricelist1.id, pricelist2.id])],
            "room_type_ids": [(6, 0, [room_type_double.id])],
            "pms_property_ids": [self.pms_property1.id],
            "start_date": date_from,
            "end_date": date_to,
        }
        # ACT
        self.env["pms.massive.changes.wizard"].create(
            vals_wizard
        ).apply_massive_changes()
        # ASSERT
        self.assertEqual(
            set(expected_pricelists),
            set(
                self.env["product.pricelist.item"]
                .search([("product_id", "=", room_type_double.product_id.id)])
                .mapped("pricelist_id")
                .ids
            ),
            "The wizard should create as many items as pricelists given.",
        )

    def test_several_room_types_pricelist(self):
        """
        If several room types are set, the wizard should create as
        many pricelist items as room types.
        """
        # ARRANGE
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        room_type_single = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Single Test",
                "default_code": "SNG_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        date_from = fields.date.today()
        date_to = fields.date.today()
        expected_product_ids = [
            room_type_double.product_id.id,
            room_type_single.product_id.id,
        ]
        vals_wizard = {
            "massive_changes_on": "pricelist",
            "pricelist_ids": [(6, 0, [self.pricelist1.id])],
            "room_type_ids": [
                (
                    6,
                    0,
                    [room_type_double.id, room_type_single.id],
                )
            ],
            "pms_property_ids": [self.pms_property1.id],
            "start_date": date_from,
            "end_date": date_to,
        }
        # ACT
        self.env["pms.massive.changes.wizard"].create(
            vals_wizard
        ).apply_massive_changes()
        # ASSERT
        self.assertEqual(
            set(expected_product_ids),
            set(
                self.env["product.pricelist.item"]
                .search([("pricelist_id", "=", self.pricelist1.id)])
                .mapped("product_id")
                .ids
            ),
            "The wizard should create as many items as room types given.",
        )

    def test_one_board_service_room_type_no_board_service(self):
        """
        Call to wizard with one board service room type and no
        board service.
        The wizard must create as many pricelist items as there
        are services on the given board service.
        """
        # ARRANGE
        room_type_single = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        board_service_only_breakfast = self.env["pms.board.service"].create(
            {
                "name": "Test Only Breakfast",
                "default_code": "CB1",
            }
        )
        service_breakfast = self.env["product.product"].create(
            {"name": "Test Breakfast"}
        )
        board_service_single = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": room_type_single.id,
                "pms_board_service_id": board_service_only_breakfast.id,
            }
        )
        board_service_line_single_1 = self.env["pms.board.service.line"].create(
            {
                "product_id": service_breakfast.id,
                "pms_board_service_id": board_service_only_breakfast.id,
            }
        )
        date_from = fields.date.today()
        date_to = fields.date.today()
        wizard_result = self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "pricelist",
                "pricelist_ids": [(6, 0, [self.pricelist1.id])],
                "apply_pricelists_on": "board_services",
                "board_service_room_type_ids": [
                    (
                        6,
                        0,
                        [board_service_single.id],
                    )
                ],
                "pms_property_ids": [self.pms_property1.id],
                "start_date": date_from,
                "end_date": date_to,
                "date_types": "consumption_dates",
            }
        )
        # ACT
        wizard_result.apply_massive_changes()

        items_created = self.env["product.pricelist.item"].search(
            [
                ("pricelist_id", "=", self.pricelist1.id),
                ("pms_property_ids", "=", self.pms_property1.id),
                ("product_id", "=", board_service_line_single_1.product_id.id),
            ]
        )
        # ASSERT
        self.assertIn(
            service_breakfast,
            items_created.mapped("product_id"),
            "The wizard must create as many pricelist items as there "
            "are services on the given board service.",
        )

    def test_one_board_service_room_type_with_board_service(self):
        """
        Call to wizard with one board service room type and
        board service.
        The wizard must create one pricelist items with
        the board service given.
        """
        # ARRANGE
        room_type_single = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        board_service_only_breakfast = self.env["pms.board.service"].create(
            {
                "name": "Test Only Breakfast",
                "default_code": "CB1",
            }
        )
        service_breakfast = self.env["product.product"].create(
            {"name": "Test Breakfast"}
        )
        board_service_single = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": room_type_single.id,
                "pms_board_service_id": board_service_only_breakfast.id,
            }
        )
        board_service_line_single_1 = self.env["pms.board.service.line"].create(
            {
                "product_id": service_breakfast.id,
                "pms_board_service_id": board_service_only_breakfast.id,
            }
        )
        date_from = fields.date.today()
        date_to = fields.date.today()
        wizard_result = self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "pricelist",
                "pricelist_ids": [(6, 0, [self.pricelist1.id])],
                "apply_pricelists_on": "board_services",
                "board_service_room_type_ids": [
                    (
                        6,
                        0,
                        [board_service_single.id],
                    )
                ],
                "board_service": board_service_line_single_1.product_id.id,
                "pms_property_ids": [self.pms_property1.id],
                "start_date": date_from,
                "end_date": date_to,
                "date_types": "consumption_dates",
            }
        )
        # ACT
        wizard_result.apply_massive_changes()

        items_created = self.env["product.pricelist.item"].search(
            [
                ("pricelist_id", "=", self.pricelist1.id),
                ("pms_property_ids", "=", self.pms_property1.id),
                ("product_id", "=", board_service_line_single_1.product_id.id),
            ]
        )
        # ASSERT
        self.assertIn(
            service_breakfast,
            items_created.mapped("product_id"),
            "The wizard must create one pricelist items with "
            " the board service given.",
        )

    def test_several_board_service_room_type_no_board_service(self):
        """
        Call to wizard with several board service room type and no
        board service.
        The wizard must create as many pricelist items as there
        are services on the given board services.
        """
        # ARRANGE
        room_type_single = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "SNG_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        board_service_only_breakfast = self.env["pms.board.service"].create(
            {
                "name": "Test Only Breakfast",
                "default_code": "CB1",
            }
        )
        board_service_half_board = self.env["pms.board.service"].create(
            {
                "name": "Test Half Board",
                "default_code": "CB2",
            }
        )
        service_breakfast = self.env["product.product"].create(
            {"name": "Test Breakfast"}
        )
        service_dinner = self.env["product.product"].create({"name": "Test Dinner"})
        board_service_single = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": room_type_single.id,
                "pms_board_service_id": board_service_only_breakfast.id,
            }
        )
        board_service_double = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": room_type_double.id,
                "pms_board_service_id": board_service_half_board.id,
            }
        )
        self.env["pms.board.service.line"].create(
            {
                "product_id": service_breakfast.id,
                "pms_board_service_id": board_service_only_breakfast.id,
            }
        )
        self.env["pms.board.service.line"].create(
            {
                "product_id": service_breakfast.id,
                "pms_board_service_id": board_service_half_board.id,
            }
        )
        self.env["pms.board.service.line"].create(
            {
                "product_id": service_dinner.id,
                "pms_board_service_id": board_service_half_board.id,
            }
        )
        date_from = fields.date.today()
        date_to = fields.date.today()
        product_ids_expected = (
            board_service_double.pms_board_service_id.board_service_line_ids.mapped(
                "product_id"
            ).ids
            + board_service_single.pms_board_service_id.board_service_line_ids.mapped(
                "product_id"
            ).ids
        )
        wizard_result = self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "pricelist",
                "pricelist_ids": [(6, 0, [self.pricelist1.id])],
                "apply_pricelists_on": "board_services",
                "board_service_room_type_ids": [
                    (
                        6,
                        0,
                        [
                            board_service_single.id,
                            board_service_double.id,
                        ],
                    )
                ],
                "pms_property_ids": [self.pms_property1.id],
                "start_date": date_from,
                "end_date": date_to,
                "date_types": "consumption_dates",
            }
        )
        # ACT
        wizard_result.apply_massive_changes()
        items_created = self.env["product.pricelist.item"].search(
            [
                ("pricelist_id", "=", self.pricelist1.id),
                ("pms_property_ids", "=", self.pms_property1.id),
                ("product_id", "in", product_ids_expected),
            ]
        )
        # ASSERT
        self.assertEqual(
            set(product_ids_expected),
            set(items_created.mapped("product_id").ids),
            "The wizard should create as many pricelist items as there"
            " are services on the given board services.",
        )

    def test_several_board_service_room_type_with_board_service(self):

        """
        Call to wizard with several board service room types and
        board service.
        The wizard must create as many pricelist items as there
        are services on the given board services.
        """
        # ARRANGE
        room_type_single = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "SNG_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        board_service_only_breakfast = self.env["pms.board.service"].create(
            {
                "name": "Test Only Breakfast",
                "default_code": "CB1",
            }
        )
        board_service_half_board = self.env["pms.board.service"].create(
            {
                "name": "Test Half Board",
                "default_code": "CB2",
            }
        )
        service_breakfast = self.env["product.product"].create(
            {"name": "Test Breakfast"}
        )
        service_dinner = self.env["product.product"].create({"name": "Test Dinner"})
        board_service_single = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": room_type_single.id,
                "pms_board_service_id": board_service_only_breakfast.id,
            }
        )
        board_service_double = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": room_type_double.id,
                "pms_board_service_id": board_service_half_board.id,
            }
        )
        self.env["pms.board.service.line"].create(
            {
                "product_id": service_breakfast.id,
                "pms_board_service_id": board_service_only_breakfast.id,
            }
        )
        self.env["pms.board.service.line"].create(
            {
                "product_id": service_breakfast.id,
                "pms_board_service_id": board_service_half_board.id,
            }
        )
        self.env["pms.board.service.line"].create(
            {
                "product_id": service_dinner.id,
                "pms_board_service_id": board_service_half_board.id,
            }
        )
        date_from = fields.date.today()
        date_to = fields.date.today()
        board_service_id_double = board_service_double.pms_board_service_id
        board_service_id_single = board_service_single.pms_board_service_id
        product_ids_expected = list(
            set(board_service_id_double.board_service_line_ids.mapped("product_id").ids)
            & set(
                board_service_id_single.board_service_line_ids.mapped("product_id").ids
            )
        )
        wizard_result = self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "pricelist",
                "pricelist_ids": [(6, 0, [self.pricelist1.id])],
                "apply_pricelists_on": "board_services",
                "board_service_room_type_ids": [
                    (
                        6,
                        0,
                        [
                            board_service_single.id,
                            board_service_double.id,
                        ],
                    )
                ],
                "board_service": service_breakfast.id,
                "pms_property_ids": [self.pms_property1.id],
                "start_date": date_from,
                "end_date": date_to,
                "date_types": "consumption_dates",
            }
        )
        # ACT
        wizard_result.apply_massive_changes()

        items_created = self.env["product.pricelist.item"].search(
            [
                ("pricelist_id", "=", self.pricelist1.id),
                ("pms_property_ids", "=", self.pms_property1.id),
                ("product_id", "in", product_ids_expected),
            ]
        )
        # ASSERT
        self.assertEqual(
            set(product_ids_expected),
            set(items_created.mapped("product_id").ids),
            "The wizard should create as many pricelist items as there"
            " are services on the given board services.",
        )

    def test_service(self):
        """
        Call to wizard with one service (product_id)
        The wizard must create one pricelist items with
        the given service (product_id).
        """
        # ARRANGE
        service_spa = self.env["product.product"].create({"name": "Test Spa"})
        date_from = fields.date.today()
        date_to = fields.date.today()
        wizard_result = self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "pricelist",
                "pricelist_ids": [(6, 0, [self.pricelist1.id])],
                "apply_pricelists_on": "service",
                "service": service_spa.id,
                "pms_property_ids": [self.pms_property1.id],
                "start_date": date_from,
                "end_date": date_to,
                "date_types": "consumption_dates",
            }
        )
        # ACT
        wizard_result.apply_massive_changes()
        items_created = self.env["product.pricelist.item"].search(
            [
                ("pricelist_id", "=", self.pricelist1.id),
                ("pms_property_ids", "=", self.pms_property1.id),
                ("product_id", "=", service_spa.id),
            ]
        )
        # ASSERT
        self.assertIn(
            service_spa.id,
            items_created.mapped("product_id").ids,
            "The wizard should create one pricelist items with"
            " the given service (product_id).",
        )

    def test_sale_dates(self):
        """
        Call to wizard with one service (product_id)
        and dates of SALE
        The wizard must create one pricelist items with
        the given service (product_id) and dates of SALE.
        """
        # ARRANGE
        service_spa = self.env["product.product"].create({"name": "Test Spa"})
        date_from = fields.date.today()
        date_to = fields.date.today()
        wizard_result = self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "pricelist",
                "pricelist_ids": [(6, 0, [self.pricelist1.id])],
                "apply_pricelists_on": "service",
                "service": service_spa.id,
                "pms_property_ids": [self.pms_property1.id],
                "start_date": date_from,
                "end_date": date_to,
                "date_types": "sale_dates",
            }
        )
        # ACT
        wizard_result.apply_massive_changes()
        items_created = self.env["product.pricelist.item"].search(
            [
                ("pricelist_id", "=", self.pricelist1.id),
                ("pms_property_ids", "=", self.pms_property1.id),
                ("product_id", "=", service_spa.id),
            ]
        )
        expected_dates = [
            datetime.datetime.combine(date_from, datetime.datetime.min.time()),
            datetime.datetime.combine(date_to, datetime.datetime.max.time()),
        ]
        # ASSERT
        self.assertEqual(
            expected_dates,
            items_created.mapped("date_start") + items_created.mapped("date_end"),
            "The wizard should create one pricelist items with"
            " the given service (product_id) and dates of sale.",
        )

    def test_several_properties_pricelist(self):
        """
        If several properties are set, the wizard should create as
        many items as properties.
        """
        # ARRANGE
        service_spa = self.env["product.product"].create({"name": "Test Spa"})
        pms_property2 = self.env["pms.property"].create(
            {
                "name": "MY 2nd PMS TEST",
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        date_from = fields.date.today()
        date_to = fields.date.today()
        expected_properties = [
            self.pms_property1.id,
            pms_property2.id,
        ]
        vals_wizard = {
            "massive_changes_on": "pricelist",
            "pricelist_ids": [(6, 0, [self.pricelist1.id])],
            "apply_pricelists_on": "service",
            "service": service_spa.id,
            "pms_property_ids": [(6, 0, [self.pms_property1.id, pms_property2.id])],
            "start_date": date_from,
            "end_date": date_to,
            "date_types": "sale_dates",
        }
        # ACT
        self.env["pms.massive.changes.wizard"].create(
            vals_wizard
        ).apply_massive_changes()
        # ASSERT
        self.assertEqual(
            set(expected_properties),
            set(
                self.env["product.pricelist.item"]
                .search([("pricelist_id", "=", self.pricelist1.id)])
                .mapped("pms_property_ids")
                .ids
            ),
            "The wizard should create as many items as properties given.",
        )
