from datetime import datetime, timedelta

from freezegun import freeze_time

from odoo.exceptions import ValidationError

from .common import TestPms


class TestPmsHousekeepingTask(TestPms):
    def setUp(self):
        super().setUp()

    def test_task_max_inheritance(self):
        # ARRANGE
        task_type = self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type Parent",
                "is_checkout": True,
            }
        )
        parent_task = self.env["pms.housekeeping.task"].create(
            {
                "name": "Parent task",
                "room_id": self.room1.id,
                "task_type_id": task_type.id,
                "task_date": datetime.today(),
            }
        )
        child_task = self.env["pms.housekeeping.task"].create(
            {
                "name": "Child task",
                "room_id": self.room1.id,
                "task_type_id": task_type.id,
                "parent_id": parent_task.id,
                "task_date": datetime.today(),
            }
        )
        # ACT & ASSERT
        with self.assertRaises(
            ValidationError,
            msg="The maximum level of inheritance between tasks should be 2",
        ):
            self.env["pms.housekeeping.task"].create(
                {
                    "name": "Grandchild task",
                    "room_id": self.room1.id,
                    "task_type_id": task_type.id,
                    "parent_id": child_task.id,
                    "task_date": datetime.today(),
                }
            )

    def test_task_with_non_housekeeper_employee(self):
        # ARRANGE
        self.job_id = self.env["hr.job"].create(
            {
                "name": "Non housekeeper job",
            }
        )
        self.employee = self.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "company_id": self.company1.id,
                "job_id": self.job_id.id,
            }
        )
        self.task_type = self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
            }
        )
        # ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="Task should be assigned to a housekeeper role"
        ):
            self.env["pms.housekeeping.task"].create(
                {
                    "name": "Task",
                    "room_id": self.room1.id,
                    "task_type_id": self.task_type.id,
                    "task_date": datetime.today(),
                    "housekeeper_ids": [(6, 0, [self.employee.id])],
                }
            )

    def test_task_with_housekeeper_employee(self):
        # ARRANGE
        self.employee = self.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "company_id": self.company1.id,
                "job_id": self.env.ref("pms_housekeeping.housekeeping_job_id").id,
            }
        )
        self.task_type = self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
            }
        )
        # ACT
        self.task = self.env["pms.housekeeping.task"].create(
            {
                "name": "Task",
                "room_id": self.room1.id,
                "task_type_id": self.task_type.id,
                "task_date": datetime.today(),
                "housekeeper_ids": [(6, 0, [self.employee.id])],
            }
        )
        # ASSERT
        self.assertTrue(self.task, "Housekeeping task should be created")

    def test_task_inconsistency_between_room_id_and_housekeeper_properties(self):
        # ARRANGE
        self.pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        self.room2 = self.env["pms.room"].create(
            {
                "name": "Room 202",
                "pms_property_id": self.pms_property2.id,
                "room_type_id": self.room_type1.id,
            }
        )
        self.employee = self.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "company_id": self.company1.id,
                "job_id": self.env.ref("pms_housekeeping.housekeeping_job_id").id,
                "property_ids": [(6, 0, [self.pms_property1.id])],
            }
        )
        self.task_type = self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
            }
        )
        # ACT & ASSERT
        with self.assertRaises(
            ValidationError,
            msg="Task with inconsistency between room_id and "
            "housekeeper properties should not be created",
        ):
            self.env["pms.housekeeping.task"].create(
                {
                    "name": "Task",
                    "room_id": self.room2.id,
                    "task_type_id": self.task_type.id,
                    "task_date": datetime.today(),
                    "housekeeper_ids": [(6, 0, [self.employee.id])],
                }
            )

    def test_task_consistency_between_room_id_and_housekeeper_properties(self):
        # ARRANGE
        self.employee = self.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "company_id": self.company1.id,
                "job_id": self.env.ref("pms_housekeeping.housekeeping_job_id").id,
                "property_ids": [(6, 0, [self.pms_property1.id])],
            }
        )
        self.task_type = self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
            }
        )
        # ACT
        task = self.env["pms.housekeeping.task"].create(
            {
                "name": "Task",
                "room_id": self.room1.id,
                "task_type_id": self.task_type.id,
                "task_date": datetime.today(),
                "housekeeper_ids": [(6, 0, [self.employee.id])],
            }
        )
        # ASSERT
        self.assertTrue(
            task,
            "Task with consistency between room_id and "
            "housekeeper properties should be created",
        )

    # Tests generate_tasks method
    @freeze_time("2000-01-10")
    def test_task_generate_tasks_create_overnight(self):
        # ARRANGE
        self.env["pms.reservation"].create(
            {
                "checkin": datetime.today(),
                "checkout": datetime.today() + timedelta(days=7),
                "room_type_id": self.room_type1.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "sale_channel_origin_id": self.sale_channel1.id,
            }
        )
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_overnight": True,
                "days_after_clean_overnight": 2,
            }
        )
        test_dates = ["2000-01-12", "2000-01-14", "2000-01-16"]
        for test_date in test_dates:
            with self.subTest(test_date=test_date):
                with freeze_time(test_date):
                    # ACT
                    self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)
                    # ASSERT
                    housekeeping_task = self.env["pms.housekeeping.task"].search(
                        [("room_id", "=", self.room1.id), ("task_date", "=", test_date)]
                    )
                    self.assertTrue(
                        housekeeping_task, "Overnight tasks should be created"
                    )

    @freeze_time("2000-01-10")
    def test_task_generate_tasks_no_create_overnight_tasks(self):
        # ARRANGE
        self.env["pms.reservation"].create(
            {
                "checkin": datetime.today(),
                "checkout": datetime.today() + timedelta(days=7),
                "room_type_id": self.room_type1.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "sale_channel_origin_id": self.sale_channel1.id,
            }
        )
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_overnight": True,
                "days_after_clean_overnight": 2,
            }
        )
        test_dates = ["2000-01-11", "2000-01-13", "2000-01-15"]
        for test_date in test_dates:
            with self.subTest(test_date=test_date):
                with freeze_time(test_date):
                    # ACT
                    self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)
                    # ASSERT
                    housekeeping_task = self.env["pms.housekeeping.task"].search(
                        [("room_id", "=", self.room1.id), ("task_date", "=", test_date)]
                    )
                    self.assertFalse(
                        housekeeping_task, "Overnight tasks shouldn't be created"
                    )

    @freeze_time("2000-01-04")
    def test_task_generate_tasks_no_create_overnight_task_no_overnight_reservations(
        self,
    ):
        # ARRANGE
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_overnight": True,
                "days_after_clean_overnight": 2,
            }
        )
        # ACT
        self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)
        # ASSERT
        housekeeping_task = self.env["pms.housekeeping.task"].search(
            [("room_id", "=", self.room1.id)]
        )
        self.assertFalse(housekeeping_task, "Empty tasks shouldn't be created")

    @freeze_time("2000-02-11")
    def test_task_generate_tasks_create_empty_tasks(self):
        # ARRANGE
        self.env["pms.reservation"].create(
            {
                "checkin": datetime.today() + timedelta(days=-20),
                "checkout": datetime.today() + timedelta(days=-10),
                "room_type_id": self.room_type1.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "sale_channel_origin_id": self.sale_channel1.id,
            }
        )
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_empty": True,
                "days_after_clean_empty": 2,
            }
        )
        test_dates = ["2000-02-03", "2000-02-05", "2000-02-07"]
        for test_date in test_dates:
            with self.subTest(test_date=test_date):
                with freeze_time(test_date):
                    # ACT
                    self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)
                    # ASSERT
                    housekeeping_task = self.env["pms.housekeeping.task"].search(
                        [("room_id", "=", self.room1.id), ("task_date", "=", test_date)]
                    )
                    self.assertTrue(housekeeping_task, "Empty tasks should be created")

    @freeze_time("2000-02-11")
    def test_task_generate_tasks_no_create_empty_tasks(self):
        # ARRANGE
        self.env["pms.reservation"].create(
            {
                "checkin": datetime.today() + timedelta(days=-20),
                "checkout": datetime.today() + timedelta(days=-10),
                "room_type_id": self.room_type1.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "sale_channel_origin_id": self.sale_channel1.id,
            }
        )
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_empty": True,
                "days_after_clean_empty": 2,
            }
        )
        test_dates = ["2000-02-02", "2000-02-04", "2000-02-06"]
        for test_date in test_dates:
            with self.subTest(test_date=test_date):
                with freeze_time(test_date):
                    # ACT
                    self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)
                    # ASSERT
                    housekeeping_task = self.env["pms.housekeeping.task"].search(
                        [("room_id", "=", self.room1.id), ("task_date", "=", test_date)]
                    )
                    self.assertFalse(
                        housekeeping_task, "Empty tasks should not be created"
                    )

    @freeze_time("2000-01-04")
    def test_task_generate_tasks_no_create_empty_task_no_previous_checkouts(self):
        # ARRANGE
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_empty": True,
                "days_after_clean_empty": 2,
            }
        )
        # ACT
        self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)
        # ASSERT
        housekeeping_task = self.env["pms.housekeeping.task"].search(
            [("room_id", "=", self.room1.id)]
        )
        self.assertFalse(housekeeping_task, "Empty tasks shouldn't be created")

    @freeze_time("2000-01-04")
    def test_task_generate_tasks_create_checkin_task(self):
        # ARRANGE
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_checkin": True,
            }
        )
        self.env["pms.reservation"].create(
            {
                "checkin": datetime.today(),
                "checkout": datetime.today() + timedelta(days=3),
                "room_type_id": self.room_type1.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "sale_channel_origin_id": self.sale_channel1.id,
            }
        )
        # ACT
        self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)
        # ASSERT
        housekeeping_task = self.env["pms.housekeeping.task"].search(
            [("room_id", "=", self.room1.id)]
        )
        self.assertTrue(housekeeping_task, "Checkin tasks should be created")

    @freeze_time("2000-01-04")
    def test_task_generate_tasks_no_create_checkin_task(self):
        # ARRANGE
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_checkin": True,
            }
        )
        # ACT
        self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)
        # ASSERT
        housekeeping_task = self.env["pms.housekeeping.task"].search(
            [("room_id", "=", self.room1.id)]
        )
        self.assertFalse(housekeeping_task, "Checkin task shouldn't be created")

    @freeze_time("2000-01-04")
    def test_task_generate_tasks_create_checkout_task(self):
        # ARRANGE
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_checkout": True,
            }
        )
        self.env["pms.reservation"].create(
            {
                "checkin": datetime.today() + timedelta(days=-3),
                "checkout": datetime.today(),
                "room_type_id": self.room_type1.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "sale_channel_origin_id": self.sale_channel1.id,
            }
        )
        # ACT
        self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)
        # ASSERT
        housekeeping_task = self.env["pms.housekeeping.task"].search(
            [("room_id", "=", self.room1.id)]
        )
        self.assertTrue(housekeeping_task, "Checkout task should be created")

    @freeze_time("2000-01-04")
    def test_task_generate_tasks_no_create_checkout_task(self):
        # ARRANGE
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_checkout": True,
            }
        )
        # ACT
        self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)
        # ASSERT
        housekeeping_task = self.env["pms.housekeeping.task"].search(
            [("room_id", "=", self.room1.id)]
        )
        self.assertFalse(housekeeping_task, "Checkout task shouldn't be created")

    @freeze_time("2000-01-04")
    def test_task_generate_tasks_create_child_task(self):
        # ARRANGE
        parent_task_type = self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type Parent",
                "is_checkout": True,
            }
        )
        child_task_type = self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type Child",
                "is_checkout": True,
                "parent_id": parent_task_type.id,
            }
        )
        self.env["pms.reservation"].create(
            {
                "checkin": datetime.today() + timedelta(days=-3),
                "checkout": datetime.today(),
                "room_type_id": self.room_type1.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "sale_channel_origin_id": self.sale_channel1.id,
            }
        )
        # ACT
        self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)
        # ASSERT
        housekeeping_task = self.env["pms.housekeeping.task"].search(
            [
                ("room_id", "=", self.room1.id),
                ("task_type_id", "=", child_task_type.id),
            ]
        )
        self.assertTrue(housekeeping_task, "Child task should be created")

    def test_task_generate_tasks_no_create_child_task(self):
        # ARRANGE
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type Parent",
                "is_checkout": True,
            }
        )
        self.env["pms.reservation"].create(
            {
                "checkin": datetime.today() + timedelta(days=-3),
                "checkout": datetime.today(),
                "room_type_id": self.room_type1.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "sale_channel_origin_id": self.sale_channel1.id,
            }
        )
        # ACT
        self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)
        # ASSERT
        housekeeping_task = self.env["pms.housekeeping.task"].search(
            [("room_id", "=", self.room1.id)]
        )
        self.assertFalse(housekeeping_task.child_ids, "Child task shouldn´t be created")
