from odoo.tests.common import TransactionCase


class TestPmsHrProperty(TransactionCase):
    def setUp(self):
        super(TestPmsHrProperty, self).setUp()
        self.PmsProperty = self.env["pms.property"]
        self.HrEmployee = self.env["hr.employee"]
        self.Company = self.env["res.company"]

        # Crear empresa
        self.company1 = self.Company.create(
            {
                "name": "Company 1",
            }
        )

        # Crear propiedad
        self.property1 = self.PmsProperty.create(
            {
                "name": "Property 1",
                "company_id": self.company1.id,
            }
        )

        # Crear usuarios
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

        # Crear empleados
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

        # Asignar la propiedad al empleado
        self.employee.write({"property_ids": [(4, self.property1.id)]})

    def test_compute_employee_ids(self):
        """Verifica que el método _compute_employee_ids
        calcule correctamente el campo employee_ids"""

        # Forzar el cálculo del campo employee_ids en property1
        self.property1._compute_employee_ids()

        # Obtener el campo calculado para property1
        assigned_employees = self.property1.employee_ids

        # Empleados esperados (los asignados a property1)
        expected_employees = self.HrEmployee.search(
            [("property_ids", "in", self.property1.id)]
        )

        # Comprobar que el campo calculado coincide con los empleados esperados
        self.assertEqual(
            sorted(assigned_employees.ids),
            sorted(expected_employees.ids),
            "Property 1 no coincide con los empleados esperados.",
        )

    def test_no_employees_assigned(self):
        """Verifica el comportamiento si no hay empleados asignados a una propiedad"""

        # Eliminar la asignación de property1 a employee
        self.employee.write({"property_ids": [(5, self.property1.id)]})

        # Forzar el cálculo del campo employee_ids en property1
        self.property1._compute_employee_ids()

        # Obtener el campo calculado para property1
        assigned_employees = self.property1.employee_ids

        # Comprobar que no haya empleados asignados a property1
        self.assertEqual(
            len(assigned_employees),
            0,
            "Se esperaba que no hubiera empleados asignados a la propiedad 1.",
        )

    def test_multiple_properties(self):
        """Verifica que los empleados se asignen correctamente a múltiples propiedades"""

        # Crear otra propiedad
        self.property2 = self.PmsProperty.create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
            }
        )

        # Asignar la propiedad 2 a el empleado 2
        self.employee2.write({"property_ids": [(4, self.property2.id)]})

        # Forzar el cálculo del campo employee_ids en property2
        self.property2._compute_employee_ids()

        # Obtener el campo calculado para property2
        assigned_employees = self.property2.employee_ids

        # Empleado esperado (asignado a property2)
        expected_employees = self.HrEmployee.search(
            [("property_ids", "in", self.property2.id)]
        )

        # Comprobar que el campo calculado coincide con los empleados esperados
        self.assertEqual(
            sorted(assigned_employees.ids),
            sorted(expected_employees.ids),
            "employee_ids calculado para la propiedad 2 no coincide con los empleados.",
        )
