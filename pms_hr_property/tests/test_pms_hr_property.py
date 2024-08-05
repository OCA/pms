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

        self.company1 = self.Company.create(
            {
                "name": "Company 1",
            }
        )
        self.property1 = self.PmsProperty.create(
            {
                "name": "Property 1",
                "company_id": self.company1.id,
            }
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
        self.employee.write({"property_ids": [(4, self.property1.id)]})

    def test_compute_employee_ids(self):
        """Verifica que el método _compute_employee_ids
        calcule correctamente el campo employee_ids"""

        self.property1._compute_employee_ids()

        assigned_employees = self.property1.employee_ids

        expected_employees = self.HrEmployee.search(
            [("property_ids", "in", self.property1.id)]
        )

        self.assertEqual(
            sorted(assigned_employees.ids),
            sorted(expected_employees.ids),
            "Property 1 no coincide con los empleados esperados.",
        )

    def test_no_employees_assigned(self):
        """Verifica el comportamiento si no hay empleados asignados a una propiedad"""

        self.employee.write({"property_ids": [(5, self.property1.id)]})

        self.property1._compute_employee_ids()
        assigned_employees = self.property1.employee_ids

        self.assertEqual(
            len(assigned_employees),
            0,
            "Se esperaba que no hubiera empleados asignados a la propiedad 1.",
        )

    def test_multiple_properties(self):
        """Verifica que los empleados se asignen correctamente a múltiples propiedades"""
        self.property2 = self.PmsProperty.create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
            }
        )

        self.employee2.write({"property_ids": [(4, self.property2.id)]})

        self.property2._compute_employee_ids()

        assigned_employees = self.property2.employee_ids

        expected_employees = self.HrEmployee.search(
            [("property_ids", "in", self.property2.id)]
        )

        self.assertEqual(
            sorted(assigned_employees.ids),
            sorted(expected_employees.ids),
            "employee_ids calculado para la propiedad 2 no coincide con los empleados.",
        )
