# Copyright 2024 OsoTranquilo - José Luis Algara
# Copyright 2024 Irlui Ramírez
# From Consultores Hoteleros Integrales (ALDA Hotels) - 2024
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase


class TestPmsHrProperty(TransactionCase):
    def setUp(self):
        super(TestPmsHrProperty, self).setUp()
        self.PmsProperty = self.env["pms.property"]
        self.HrEmployee = self.env["hr.employee"]
        self.Company = self.env["res.company"]

        self.company1 = self.Company.create({"name": "Company 1"})

        self.property1 = self.PmsProperty.create(
            {"name": "Property 1", "company_id": self.company1.id}
        )

        user_dict = {
            "name": "User 1",
            "login": "tua@example.com",
            "password": "base-test-passwd",
        }
        self.user_test = self.env["res.users"].create(user_dict)

        user_dict2 = {
            "name": "User 2",
            "login": "user2@example.com",
            "password": "base-test-passwd",
        }
        self.user_test2 = self.env["res.users"].create(user_dict2)

        employee_dict = {
            "name": "Employee 1",
            "user_id": self.user_test.id,
            "address_id": self.user_test.partner_id.id,
        }
        self.employee = self.env["hr.employee"].create(employee_dict)

        employee_dict2 = {
            "name": "Employee 2",
            "user_id": self.user_test2.id,
            "address_id": self.user_test2.partner_id.id,
        }
        self.employee2 = self.env["hr.employee"].create(employee_dict2)

    def test_employee_assignment(self):
        """Check if employees are correctly assigned to properties"""
        self.employee.write({"property_ids": [(4, self.property1.id)]})

        assigned_employees = self.property1.employee_ids
        self.assertIn(
            self.employee,
            assigned_employees,
            "The employee is not correctly assigned to the property.",
        )

    def test_employee_removal(self):
        """Check if employees can be unassigned from properties correctly"""
        self.employee.write({"property_ids": [(4, self.property1.id)]})

        self.employee.write({"property_ids": [(3, self.property1.id)]})

        assigned_employees = self.property1.employee_ids
        self.assertNotIn(
            self.employee,
            assigned_employees,
            "The employee is still assigned to the property after removal.",
        )

    def test_multiple_employees_assignment(self):
        """Check if multiple employees can be assigned to a single property"""
        self.employee.write({"property_ids": [(4, self.property1.id)]})
        self.employee2.write({"property_ids": [(4, self.property1.id)]})

        assigned_employees = self.property1.employee_ids
        self.assertIn(
            self.employee, assigned_employees, "Employee 1 is not correctly assigned."
        )
        self.assertIn(
            self.employee2, assigned_employees, "Employee 2 is not correctly assigned."
        )
