# Copyright (C) 2022 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class TestProjectTask(TransactionCase):
    def setUp(self):
        super(TestProjectTask, self).setUp()
        user_group_employee = self.env.ref("base.group_user")
        user_group_project_user = self.env.ref("project.group_project_user")
        self.partner_1 = self.env["res.partner"].create(
            {"name": "Valid Lelitre", "email": "valid.lelitre@agrolait.com"}
        )
        self.project_pigs = (
            self.env["project.project"]
            .with_context({"mail_create_nolog": True})
            .create(
                {
                    "name": "Pigs",
                    "privacy_visibility": "employees",
                    "alias_name": "project+pigs",
                    "partner_id": self.partner_1.id,
                }
            )
        )
        self.user_projectuser = (
            self.env["res.users"]
            .with_context({"no_reset_password": True})
            .create(
                {
                    "name": "Armande ProjectUser",
                    "login": "Armande",
                    "email": "armande.projectuser@example.com",
                    "groups_id": [
                        (6, 0, [user_group_employee.id, user_group_project_user.id])
                    ],
                }
            )
        )
        self.testtask = self.task_1 = (
            self.env["project.task"]
            .with_context({"mail_create_nolog": True})
            .create(
                {
                    "name": "Pigs UserTask",
                    "user_id": self.user_projectuser.id,
                    "project_id": self.project_pigs.id,
                }
            )
        )
        self.testproperty = self.env["pms.property"].create(
            {"name": "test property", "owner_id": self.partner_1.id}
        )
        self.testproperty2 = self.env["pms.property"].create(
            {"name": "test property2", "owner_id": self.partner_1.id}
        )

    def test_project_task_m2m(self):
        self.testtask.pms_property_ids = [
            (6, 0, [self.testproperty.id, self.testproperty2.id])
        ]
        self.assertEqual(
            self.testproperty.id in self.testtask.pms_property_ids.ids, True
        )
