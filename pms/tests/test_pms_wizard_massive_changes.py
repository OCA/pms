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
        self.test_room_type_double = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.test_property.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": self.test_room_type_class.id,
            }
        )

        # pms.board.service
        self.test_board_service_only_breakfast = self.env["pms.board.service"].create(
            {
                "name": "Test Only Breakfast",
                "default_code": "CB1",
            }
        )
        self.test_board_service_half_board = self.env["pms.board.service"].create(
            {
                "name": "Test Half Board",
                "default_code": "CB2",
            }
        )
        # product.product 1
        self.test_service_breakfast = self.env["product.product"].create(
            {"name": "Test Breakfast"}
        )
        self.test_service_dinner = self.env["product.product"].create(
            {"name": "Test Dinner"}
        )
        self.test_service_spa = self.env["product.product"].create({"name": "Test Spa"})
        # pms.board.service.room.type
        self.test_board_service_single = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.test_room_type_single.id,
                "pms_board_service_id": self.test_board_service_only_breakfast.id,
            }
        )
        self.test_board_service_double = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.test_room_type_double.id,
                "pms_board_service_id": self.test_board_service_half_board.id,
            }
        )
        # pms.board.service.line
        self.board_service_line_single_1 = self.env["pms.board.service.line"].create(
            {
                "product_id": self.test_service_breakfast.id,
                "pms_board_service_id": self.test_board_service_only_breakfast.id,
            }
        )
        self.board_service_line_double_1 = self.env["pms.board.service.line"].create(
            {
                "product_id": self.test_service_breakfast.id,
                "pms_board_service_id": self.test_board_service_half_board.id,
            }
        )
        self.board_service_line_double_2 = self.board_service_line = self.env[
            "pms.board.service.line"
        ].create(
            {
                "product_id": self.test_service_dinner.id,
                "pms_board_service_id": self.test_board_service_half_board.id,
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
                        "availability_plan_ids": [
                            (6, 0, [self.test_availability_plan.id])
                        ],
                        "start_date": fields.date.today(),
                        "end_date": fields.date.today() + datetime.timedelta(days=days),
                        "room_type_ids": [(6, 0, [self.test_room_type_double.id])],
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
                "availability_plan_ids": [(6, 0, [self.test_availability_plan.id])],
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
            "availability_plan_ids": [(6, 0, [self.test_availability_plan.id])],
            "start_date": date_from,
            "end_date": date_to,
            "room_type_ids": [(6, 0, [self.test_room_type_double.id])],
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
        del vals["availability_plan_ids"]
        del vals["start_date"]
        del vals["end_date"]
        del vals["room_type_ids"]
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
                "availability_plan_ids": [(6, 0, [self.test_availability_plan.id])],
                "room_type_ids": [(6, 0, [self.test_room_type_double.id])],
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
            "availability_plan_ids": [(6, 0, [self.test_availability_plan.id])],
            "start_date": date,
            "end_date": date,
            "room_type_ids": [(6, 0, [self.test_room_type_double.id])],
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

    @freeze_time("2025-12-01")
    def test_several_availability_plan(self):
        # TEST CASE
        # If several availability plans are set, the wizard should create as
        # many rules as availability plans.

        # ARRANGE
        self.create_common_scenario()
        self.test_availability_plan_2 = self.env["pms.availability.plan"].create(
            {
                "name": "Second availability plan for TEST",
                "pms_pricelist_ids": [self.test_pricelist.id],
            }
        )
        expected_av_plans = [
            self.test_availability_plan.id,
            self.test_availability_plan_2.id,
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
                        self.test_availability_plan.id,
                        self.test_availability_plan_2.id,
                    ],
                )
            ],
            "room_type_ids": [(6, 0, [self.test_room_type_double.id])],
            "pms_property_ids": [self.test_property.id],
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
                .search([("room_type_id", "=", self.test_room_type_double.id)])
                .mapped("availability_plan_id")
                .ids
            ),
            "The wizard should create as many rules as availability plans given.",
        )

    @freeze_time("2025-02-01")
    def test_several_room_types_availability_plan(self):
        # TEST CASE
        # If several room types are set, the wizard should create as
        # many rules as room types.

        # ARRANGE
        self.create_common_scenario()
        self.test_availability_plan_2 = self.env["pms.availability.plan"].create(
            {
                "name": "Second availability plan for TEST",
                "pms_pricelist_ids": [self.test_pricelist.id],
            }
        )
        expected_room_types = [
            self.test_room_type_double.id,
            self.test_room_type_single.id,
        ]
        date_from = fields.date.today()
        date_to = fields.date.today()
        vals_wizard = {
            "massive_changes_on": "availability_plan",
            "availability_plan_ids": [(6, 0, [self.test_availability_plan.id])],
            "room_type_ids": [
                (
                    6,
                    0,
                    [self.test_room_type_double.id, self.test_room_type_single.id],
                )
            ],
            "pms_property_ids": [self.test_property.id],
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
                .search([("availability_plan_id", "=", self.test_availability_plan.id)])
                .mapped("room_type_id")
                .ids
            ),
            "The wizard should create as many rules as room types given.",
        )

    @freeze_time("1980-12-01")
    def test_several_properties_availability_plan(self):
        # TEST CASE
        # If several properties are set, the wizard should create as
        # many rules as properties.

        # ARRANGE
        self.create_common_scenario()
        self.test_property2 = self.env["pms.property"].create(
            {
                "name": "MY 2nd PMS TEST",
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        self.test_room_type_double.pms_property_ids = [
            (6, 0, [self.test_property.id, self.test_property2.id])
        ]
        expected_properties = [
            self.test_property.id,
            self.test_property2.id,
        ]
        date_from = fields.date.today()
        date_to = fields.date.today()
        vals_wizard = {
            "massive_changes_on": "availability_plan",
            "availability_plan_ids": [(6, 0, [self.test_availability_plan.id])],
            "room_type_ids": [(6, 0, [self.test_room_type_double.id])],
            "pms_property_ids": [
                (6, 0, [self.test_property.id, self.test_property2.id])
            ],
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
                .search([("availability_plan_id", "=", self.test_availability_plan.id)])
                .mapped("pms_property_id")
                .ids
            ),
            "The wizard should create as many rules as properties given.",
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
                        "pricelist_ids": [(6, 0, [self.test_pricelist.id])],
                        "start_date": fields.date.today(),
                        "end_date": fields.date.today() + datetime.timedelta(days=days),
                        "room_type_ids": [(6, 0, [self.test_room_type_double.id])],
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
                "pricelist_ids": [(6, 0, [self.test_pricelist.id])],
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
                "pricelist_ids": [(6, 0, [self.test_pricelist.id])],
                "start_date": date_from,
                "end_date": date_to,
                "room_type_ids": [(6, 0, [self.test_room_type_double.id])],
                "price": price,
                "min_quantity": min_quantity,
                "pms_property_ids": [self.test_property.id],
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
                "pricelist_ids": [(6, 0, [self.test_pricelist.id])],
                "room_type_ids": [(6, 0, [self.test_room_type_double.id])],
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
                    key=lambda s: s.date_start_consumption
                )

                # ASSERT
                self.assertTrue(
                    pricelist_items[index].date_start_consumption.timetuple()[6]
                    == index
                    and test_case[index],
                    "Rule not created on correct day of week",
                )

    @freeze_time("2025-01-01")
    def test_several_pricelists(self):
        # TEST CASE
        # If several pricelist are set, the wizard should create as
        # many items as pricelists.

        # ARRANGE
        self.create_common_scenario()
        self.test_pricelist_2 = self.env["product.pricelist"].create(
            {
                "name": "test pricelist 2",
            }
        )
        expected_pricelists = [self.test_pricelist.id, self.test_pricelist_2.id]

        date_from = fields.date.today()
        date_to = fields.date.today()
        vals_wizard = {
            "massive_changes_on": "pricelist",
            "pricelist_ids": [
                (6, 0, [self.test_pricelist.id, self.test_pricelist_2.id])
            ],
            "room_type_ids": [(6, 0, [self.test_room_type_double.id])],
            "pms_property_ids": [self.test_property.id],
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
                .search([("product_id", "=", self.test_room_type_double.product_id.id)])
                .mapped("pricelist_id")
                .ids
            ),
            "The wizard should create as many items as pricelists given.",
        )

    @freeze_time("2025-02-01")
    def test_several_room_types_pricelist(self):
        # TEST CASE
        # If several room types are set, the wizard should create as
        # many items as room types.

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today()
        date_to = fields.date.today()
        expected_product_ids = [
            self.test_room_type_double.product_id.id,
            self.test_room_type_single.product_id.id,
        ]
        vals_wizard = {
            "massive_changes_on": "pricelist",
            "pricelist_ids": [(6, 0, [self.test_pricelist.id])],
            "room_type_ids": [
                (
                    6,
                    0,
                    [self.test_room_type_double.id, self.test_room_type_single.id],
                )
            ],
            "pms_property_ids": [self.test_property.id],
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
                .search([("pricelist_id", "=", self.test_pricelist.id)])
                .mapped("product_id")
                .ids
            ),
            "The wizard should create as many items as room types given.",
        )

    @freeze_time("2025-02-01")
    def test_one_board_service_room_type_no_board_service(self):
        # TEST CASE
        # Call to wizard with one board service room type and no
        # board service.
        # The wizard must create as many pricelist items as there
        # are services on the given board service.

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today()
        date_to = fields.date.today()
        wizard_result = self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "pricelist",
                "pricelist_ids": [(6, 0, [self.test_pricelist.id])],
                "apply_pricelists_on": "board_services",
                "board_service_room_type_ids": [
                    (
                        6,
                        0,
                        [self.test_board_service_single.id],
                    )
                ],
                "pms_property_ids": [self.test_property.id],
                "start_date": date_from,
                "end_date": date_to,
                "date_types": "consumption_dates",
            }
        )
        # ACT
        wizard_result.apply_massive_changes()

        items_created = self.env["product.pricelist.item"].search(
            [
                ("pricelist_id", "=", self.test_pricelist.id),
                ("pms_property_ids", "=", self.test_property.id),
                ("product_id", "=", self.board_service_line_single_1.product_id.id),
            ]
        )
        # ASSERT
        self.assertIn(
            self.test_service_breakfast,
            items_created.mapped("product_id"),
            "The wizard must create as many pricelist items as there "
            "are services on the given board service.",
        )

    @freeze_time("2025-02-01")
    def test_one_board_service_room_type_with_board_service(self):
        # TEST CASE
        # Call to wizard with one board service room type and
        # board service.
        # The wizard must create one pricelist items with
        # the board service given.

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today()
        date_to = fields.date.today()
        wizard_result = self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "pricelist",
                "pricelist_ids": [(6, 0, [self.test_pricelist.id])],
                "apply_pricelists_on": "board_services",
                "board_service_room_type_ids": [
                    (
                        6,
                        0,
                        [self.test_board_service_single.id],
                    )
                ],
                "board_service": self.board_service_line_single_1.product_id.id,
                "pms_property_ids": [self.test_property.id],
                "start_date": date_from,
                "end_date": date_to,
                "date_types": "consumption_dates",
            }
        )
        # ACT
        wizard_result.apply_massive_changes()

        items_created = self.env["product.pricelist.item"].search(
            [
                ("pricelist_id", "=", self.test_pricelist.id),
                ("pms_property_ids", "=", self.test_property.id),
                ("product_id", "=", self.board_service_line_single_1.product_id.id),
            ]
        )
        # ASSERT
        self.assertIn(
            self.test_service_breakfast,
            items_created.mapped("product_id"),
            "The wizard must create one pricelist items with "
            " the board service given.",
        )

    @freeze_time("2025-02-01")
    def test_several_board_service_room_type_no_board_service(self):
        # TEST CASE
        # Call to wizard with several board service room type and no
        # board service.
        # The wizard must create as many pricelist items as there
        # are services on the given board services.

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today()
        date_to = fields.date.today()
        product_ids_expected = (
            self.test_board_service_double.pms_board_service_id.board_service_line_ids.mapped(
                "product_id"
            ).ids
            + self.test_board_service_single.pms_board_service_id.board_service_line_ids.mapped(
                "product_id"
            ).ids
        )
        wizard_result = self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "pricelist",
                "pricelist_ids": [(6, 0, [self.test_pricelist.id])],
                "apply_pricelists_on": "board_services",
                "board_service_room_type_ids": [
                    (
                        6,
                        0,
                        [
                            self.test_board_service_single.id,
                            self.test_board_service_double.id,
                        ],
                    )
                ],
                "pms_property_ids": [self.test_property.id],
                "start_date": date_from,
                "end_date": date_to,
                "date_types": "consumption_dates",
            }
        )
        # ACT
        wizard_result.apply_massive_changes()

        items_created = self.env["product.pricelist.item"].search(
            [
                ("pricelist_id", "=", self.test_pricelist.id),
                ("pms_property_ids", "=", self.test_property.id),
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

    @freeze_time("2025-02-01")
    def test_several_board_service_room_type_with_board_service(self):
        # TEST CASE
        # Call to wizard with several board service room types and
        # board service.
        # The wizard must create as many pricelist items as there
        # are services on the given board services.

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today()
        date_to = fields.date.today()
        board_service_id_double = self.test_board_service_double.pms_board_service_id
        board_service_id_single = self.test_board_service_single.pms_board_service_id
        product_ids_expected = list(
            set(board_service_id_double.board_service_line_ids.mapped("product_id").ids)
            & set(
                board_service_id_single.board_service_line_ids.mapped("product_id").ids
            )
        )
        wizard_result = self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "pricelist",
                "pricelist_ids": [(6, 0, [self.test_pricelist.id])],
                "apply_pricelists_on": "board_services",
                "board_service_room_type_ids": [
                    (
                        6,
                        0,
                        [
                            self.test_board_service_single.id,
                            self.test_board_service_double.id,
                        ],
                    )
                ],
                "board_service": self.test_service_breakfast.id,
                "pms_property_ids": [self.test_property.id],
                "start_date": date_from,
                "end_date": date_to,
                "date_types": "consumption_dates",
            }
        )
        # ACT
        wizard_result.apply_massive_changes()

        items_created = self.env["product.pricelist.item"].search(
            [
                ("pricelist_id", "=", self.test_pricelist.id),
                ("pms_property_ids", "=", self.test_property.id),
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

    @freeze_time("2025-02-01")
    def test_service(self):
        # TEST CASE
        # Call to wizard with one service (product_id)
        # The wizard must create one pricelist items with
        # the given service (product_id).

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today()
        date_to = fields.date.today()
        wizard_result = self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "pricelist",
                "pricelist_ids": [(6, 0, [self.test_pricelist.id])],
                "apply_pricelists_on": "service",
                "service": self.test_service_spa.id,
                "pms_property_ids": [self.test_property.id],
                "start_date": date_from,
                "end_date": date_to,
                "date_types": "consumption_dates",
            }
        )
        # ACT
        wizard_result.apply_massive_changes()

        items_created = self.env["product.pricelist.item"].search(
            [
                ("pricelist_id", "=", self.test_pricelist.id),
                ("pms_property_ids", "=", self.test_property.id),
                ("product_id", "=", self.test_service_spa.id),
            ]
        )
        # ASSERT
        self.assertIn(
            self.test_service_spa.id,
            items_created.mapped("product_id").ids,
            "The wizard should create one pricelist items with"
            " the given service (product_id).",
        )

    @freeze_time("2025-02-01")
    def test_sale_dates(self):
        # TEST CASE
        # Call to wizard with one service (product_id)
        # and dates of SALE
        # The wizard must create one pricelist items with
        # the given service (product_id) and dates of SALE.

        # ARRANGE
        self.create_common_scenario()
        date_from = fields.date.today()
        date_to = fields.date.today()
        wizard_result = self.env["pms.massive.changes.wizard"].create(
            {
                "massive_changes_on": "pricelist",
                "pricelist_ids": [(6, 0, [self.test_pricelist.id])],
                "apply_pricelists_on": "service",
                "service": self.test_service_spa.id,
                "pms_property_ids": [self.test_property.id],
                "start_date": date_from,
                "end_date": date_to,
                "date_types": "sale_dates",
            }
        )
        # ACT
        wizard_result.apply_massive_changes()

        items_created = self.env["product.pricelist.item"].search(
            [
                ("pricelist_id", "=", self.test_pricelist.id),
                ("pms_property_ids", "=", self.test_property.id),
                ("product_id", "=", self.test_service_spa.id),
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
        # TEST CASE
        # If several properties are set, the wizard should create as
        # many items as properties.

        # ARRANGE
        self.create_common_scenario()
        self.test_property2 = self.env["pms.property"].create(
            {
                "name": "MY 2nd PMS TEST",
                "company_id": self.env.ref("base.main_company").id,
            }
        )
        date_from = fields.date.today()
        date_to = fields.date.today()
        expected_properties = [
            self.test_property.id,
            self.test_property2.id,
        ]
        vals_wizard = {
            "massive_changes_on": "pricelist",
            "pricelist_ids": [(6, 0, [self.test_pricelist.id])],
            "apply_pricelists_on": "service",
            "service": self.test_service_spa.id,
            "pms_property_ids": [
                (6, 0, [self.test_property.id, self.test_property2.id])
            ],
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
                .search([("pricelist_id", "=", self.test_pricelist.id)])
                .mapped("pms_property_ids")
                .ids
            ),
            "The wizard should create as many items as properties given.",
        )
