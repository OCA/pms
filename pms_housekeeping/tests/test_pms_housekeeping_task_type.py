from odoo.exceptions import ValidationError

from .common import TestPms


class TestPmsHousekeepingTask(TestPms):
    def setUp(self):
        super().setUp()

    def test_days_after_clean_overnight_constraint(self):
        # ARRANGE, ACT & ASSERT
        # create task type and verify that the constraint is raised
        with self.assertRaises(
            ValidationError, msg="Days After Clean Overnight should be greater than 0"
        ):
            self.env["pms.housekeeping.task.type"].create(
                {
                    "name": "Task Type 1",
                    "is_overnight": True,
                    "days_after_clean_overnight": 0,
                }
            )

    def test_days_after_clean_empty_constraint(self):
        # ARRANGE, ACT & ASSERT
        # create task type and verify that the constraint is raised
        with self.assertRaises(
            ValidationError, msg="Days After Clean Overnight should be greater than 0"
        ):
            self.env["pms.housekeeping.task.type"].create(
                {
                    "name": "Task Type 1",
                    "is_empty": True,
                    "days_after_clean_empty": 0,
                }
            )

    def test_no_create_grandchild_task_type(self):
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
        # ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="Grandchild task type shouldn´t exist."
        ):
            self.env["pms.housekeeping.task.type"].create(
                {
                    "name": "Task Type Grandchild",
                    "is_checkout": True,
                    "parent_id": child_task_type.id,
                }
            )
