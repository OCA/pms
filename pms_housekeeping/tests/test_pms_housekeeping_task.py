from datetime import datetime, timedelta

from freezegun import freeze_time

from odoo.exceptions import ValidationError

from .common import TestPms


class TestPmsHousekeepingTask(TestPms):
    def setUp(self):
        super().setUp()

    @freeze_time("2000-01-04")
    def test_no_create_overnight_task_when_it_shouldnt_when_no_overnight(self):
        # ARRANGE
        # create task type
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_overnight": True,
                "days_after_clean_overnight": 2,
            }
        )

        # ACT
        # call method to create task
        self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)

        # ASSERT
        # search for the task
        housekeeping_task = self.env["pms.housekeeping.task"].search(
            [("room_id", "=", self.room1.id)]
        )
        # Verify that the housekeeping task is not created
        self.assertFalse(housekeeping_task, "Housekeeping task shouldn't be created")

    @freeze_time("2000-01-10")
    def test_create_overnight_task_when_it_should_be_created_with_different_dates(self):
        # ARRANGE
        # create reservation with checkin today
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
        # create task type
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_overnight": True,
                "days_after_clean_overnight": 2,
            }
        )
        # Define a list of dates to iterate over
        test_dates = [
            "2000-01-12",
            "2000-01-14",
            "2000-01-16",
        ]
        for test_date in test_dates:
            with self.subTest(test_date=test_date):
                # Freeze time to the current test date
                with freeze_time(test_date):
                    # ACT
                    # call method to create task
                    self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)

                    # ASSERT
                    # search for the task
                    housekeeping_task = self.env["pms.housekeeping.task"].search(
                        [("room_id", "=", self.room1.id), ("task_date", "=", test_date)]
                    )
                    # Verify that the housekeeping task is created
                    self.assertTrue(
                        housekeeping_task, "Housekeeping task should be created"
                    )

    @freeze_time("2000-01-10")
    def test_create_overnight_task_when_it_shouldnt_be_created_with_different_dates(
        self,
    ):
        # ARRANGE
        # create reservation with checkin today
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
        # create task type
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_overnight": True,
                "days_after_clean_overnight": 2,
            }
        )
        # Define a list of dates to iterate over
        test_dates = [
            "2000-01-11",
            "2000-01-13",
            "2000-01-15",
        ]
        for test_date in test_dates:
            with self.subTest(test_date=test_date):
                # Freeze time to the current test date
                with freeze_time(test_date):
                    # ACT
                    # call method to create task
                    self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)

                    # ASSERT
                    # search for the task
                    housekeeping_task = self.env["pms.housekeeping.task"].search(
                        [("room_id", "=", self.room1.id), ("task_date", "=", test_date)]
                    )
                    # Verify that the housekeeping task is created
                    self.assertFalse(
                        housekeeping_task, "Housekeeping task shouldn't be created"
                    )

    ###################
    @freeze_time("2000-01-04")
    def test_no_create_empty_task_when_it_shouldnt_when_no_empty(self):
        # ARRANGE
        # create task type
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_empty": True,
                "days_after_clean_empty": 2,
            }
        )

        # ACT
        # call method to create task
        self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)

        # ASSERT
        # search for the task
        housekeeping_task = self.env["pms.housekeeping.task"].search(
            [("room_id", "=", self.room1.id)]
        )
        # Verify that the housekeeping task is not created
        self.assertFalse(housekeeping_task, "Housekeeping task shouldn't be created")

    @freeze_time("2000-02-11")
    def test_create_empty_task_when_it_should_be_created_with_different_dates(self):
        # ARRANGE
        # create reservation with checkout today - 10 days
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
        # create task type
        self.env["pms.housekeeping.task.type"].create(
            {"name": "Task Type 1", "is_empty": True, "days_after_clean_empty": 2}
        )
        # Define a list of dates to iterate over
        test_dates = [
            "2000-02-03",
            "2000-02-05",
            "2000-02-07",
        ]
        for test_date in test_dates:
            with self.subTest(test_date=test_date):
                # Freeze time to the current test date
                with freeze_time(test_date):
                    # ACT
                    # call method to create task
                    self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)

                    # ASSERT
                    # search for the task
                    housekeeping_task = self.env["pms.housekeeping.task"].search(
                        [("room_id", "=", self.room1.id), ("task_date", "=", test_date)]
                    )
                    # Verify that the housekeeping task is created
                    self.assertTrue(
                        housekeeping_task, "Housekeeping task should be created"
                    )

    @freeze_time("2000-02-11")
    def test_create_empty_task_when_it_shouldnt_be_created_with_different_dates(self):
        # ARRANGE
        # create reservation with checkout today - 10 days
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
        # create task type
        self.env["pms.housekeeping.task.type"].create(
            {"name": "Task Type 1", "is_empty": True, "days_after_clean_empty": 2}
        )
        # Define a list of dates to iterate over
        test_dates = [
            "2000-02-02",
            "2000-02-04",
            "2000-02-06",
        ]
        for test_date in test_dates:
            with self.subTest(test_date=test_date):
                # Freeze time to the current test date
                with freeze_time(test_date):
                    # ACT
                    # call method to create task
                    self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)

                    # ASSERT
                    # search for the task
                    housekeeping_task = self.env["pms.housekeeping.task"].search(
                        [("room_id", "=", self.room1.id), ("task_date", "=", test_date)]
                    )
                    # Verify that the housekeeping task is created
                    self.assertFalse(
                        housekeeping_task, "Housekeeping task should be created"
                    )

    @freeze_time("2000-01-04")
    def test_create_checkin_task_when_it_should_when_checkin(self):
        # ARRANGE
        # create task type
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_checkin": True,
            }
        )
        # create reservation with checkin today
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
        # call method to create task
        self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)

        # ASSERT
        # search for the task
        housekeeping_task = self.env["pms.housekeeping.task"].search(
            [("room_id", "=", self.room1.id)]
        )
        # Verify that the housekeeping task is not created
        self.assertTrue(housekeeping_task, "Housekeeping task should be created")

    @freeze_time("2000-01-04")
    def test_no_create_checkin_task_when_it_shouldnt_when_no_checkin(self):
        # ARRANGE
        # create task type
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_checkin": True,
            }
        )

        # ACT
        # call method to create task
        self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)

        # ASSERT
        # search for the task
        housekeeping_task = self.env["pms.housekeeping.task"].search(
            [("room_id", "=", self.room1.id)]
        )
        # Verify that the housekeeping task is not created
        self.assertFalse(housekeeping_task, "Housekeeping task shouldn't be created")

    @freeze_time("2000-01-04")
    def test_create_checkout_task_when_it_should_when_checkout(self):
        # ARRANGE
        # create task type
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_checkout": True,
            }
        )
        # create reservation with checkout today
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
        # call method to create task
        self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)

        # ASSERT
        # search for the task
        housekeeping_task = self.env["pms.housekeeping.task"].search(
            [("room_id", "=", self.room1.id)]
        )
        # Verify that the housekeeping task is not created
        self.assertTrue(housekeeping_task, "Housekeeping task should be created")

    @freeze_time("2000-01-04")
    def test_no_create_checkout_task_when_it_shouldnt_when_no_checkout(self):
        # ARRANGE
        # create task type
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_checkout": True,
            }
        )

        # ACT
        # call method to create task
        self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)

        # ASSERT
        # search for the task
        housekeeping_task = self.env["pms.housekeeping.task"].search(
            [("room_id", "=", self.room1.id)]
        )
        # Verify that the housekeeping task is not created
        self.assertFalse(housekeeping_task, "Housekeeping task shouldn't be created")

    @freeze_time("2000-01-04")
    def test_create_task_childs(self):
        # ARRANGE
        # create task type
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
        # create reservation with checkout today
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
        # call method to create task
        self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)

        # ASSERT
        # search for the task
        housekeeping_task = self.env["pms.housekeeping.task"].search(
            [("room_id", "=", self.room1.id), ("task_type_id", "=", child_task_type.id)]
        )
        # Verify that the housekeeping task is not created
        self.assertTrue(housekeeping_task, "Child housekeeping task should be created")

    def test_no_create_task_childs(self):
        # ARRANGE
        # create task type
        self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type Parent",
                "is_checkout": True,
            }
        )

        # create reservation with checkout today
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
        # call method to create task
        self.env["pms.housekeeping.task"].generate_tasks(self.pms_property1)

        # ASSERT
        # search for the task
        housekeeping_task = self.env["pms.housekeeping.task"].search(
            [("room_id", "=", self.room1.id)]
        )
        # Verify that the housekeeping task childs is not created
        self.assertFalse(
            housekeeping_task.child_ids, "Child housekeeping task shouldn´t be created"
        )

    def test_no_create_grandchild_task(self):
        # ARRANGE
        # create task type
        task_type = self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type Parent",
                "is_checkout": True,
            }
        )
        parent_task = self.env["pms.housekeeping.task"].create(
            {
                "name": "Task",
                "room_id": self.room1.id,
                "task_type_id": task_type.id,
                "task_date": datetime.today(),
            }
        )
        child_task = self.env["pms.housekeeping.task"].create(
            {
                "name": "Child Task",
                "room_id": self.room1.id,
                "task_type_id": task_type.id,
                "parent_id": parent_task.id,
                "task_date": datetime.today(),
            }
        )
        # ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="Grandchild task shouldn´t exist."
        ):
            self.env["pms.housekeeping.task"].create(
                {
                    "name": "Grandchild Task",
                    "room_id": self.room1.id,
                    "task_type_id": task_type.id,
                    "parent_id": child_task.id,
                    "task_date": datetime.today(),
                }
            )

    def test_create_task_with_no_housekeeper(self):

        # ARRANGE
        self.job_id = self.env["hr.job"].create(
            {
                "name": "Test Job",
            }
        )
        self.employee = self.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "company_id": self.company1.id,
                "job_id": self.job_id.id,
            }
        )
        # create task type
        self.task_type = self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_checkout": True,
            }
        )

        # ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="Employee should have a housekeeper job"
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

    def test_create_task_with_housekeeper(self):

        # ARRANGE
        self.employee = self.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "company_id": self.company1.id,
                "job_id": self.env.ref("pms_housekeeping.housekeeping_job_id").id,
            }
        )
        # create task type
        self.task_type = self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_checkout": True,
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

        #ASSERT
        self.assertTrue(self.task, "Housekeeping task should be created")

    def test_task_housekeeper_room_inconsistency(self):

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
            # create task type
            self.task_type = self.env["pms.housekeeping.task.type"].create(
                {
                    "name": "Task Type 1",
                    "is_checkout": True,
                }
            )

            # ACT & ASSERT
            with self.assertRaises(
                ValidationError, msg="The room and housekeeper should belong to the same property."
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

    def test_task_housekeeper_room_consistency(self):
        # ARRANGE
        self.employee = self.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "company_id": self.company1.id,
                "job_id": self.env.ref("pms_housekeeping.housekeeping_job_id").id,
                "property_ids": [(6, 0, [self.pms_property1.id])],
            }
        )
        # create task type
        self.task_type = self.env["pms.housekeeping.task.type"].create(
            {
                "name": "Task Type 1",
                "is_checkout": True,
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
        self.assertTrue(task, "Housekeeping task should be created")
