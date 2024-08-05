from odoo.tests.common import TransactionCase


class TestPmsHrProperty(TransactionCase):
    def setUp(self):
        super(TestPmsHrProperty, self).setUp()
        self.PmsProperty = self.env["pms.property"]
        self.HrEmployee = self.env["hr.employee"]
        self.HrJob = self.env["hr.job"]

        # Create jobs
        self.job_regional_manager = self.HrJob.create({"name": "Regional Manager"})
        self.job_revenue_manager = self.HrJob.create({"name": "Revenue Manager"})
        self.job_taz = self.HrJob.create({"name": "TAZ"})
        self.job_tmz = self.HrJob.create({"name": "TMZ"})

        # Create employees
        self.employee_1 = self.HrEmployee.create(
            {"name": "Employee 1", "job_id": self.job_regional_manager.id}
        )
        self.employee_2 = self.HrEmployee.create(
            {"name": "Employee 2", "job_id": self.job_revenue_manager.id}
        )
        self.employee_3 = self.HrEmployee.create(
            {"name": "Employee 3", "job_id": self.job_taz.id}
        )
        self.employee_4 = self.HrEmployee.create(
            {"name": "Employee 4", "job_id": self.job_tmz.id}
        )

        # Create property
        self.property = self.PmsProperty.create({"name": "Test Property"})

        # Assign employees to property
        self.employee_1.write({"property_ids": [(4, self.property.id)]})
        self.employee_2.write({"property_ids": [(4, self.property.id)]})
        self.employee_3.write({"property_ids": [(4, self.property.id)]})
        self.employee_4.write({"property_ids": [(4, self.property.id)]})

    def test_assigned_employees(self):
        """Test that the employees are correctly assigned to the property"""
        self.property._compute_employee_ids()

        assigned_employees = self.property.employee_ids
        expected_employees = self.HrEmployee.search(
            [("property_ids", "in", self.property.id)]
        )

        self.assertEqual(
            assigned_employees,
            expected_employees,
            "The assigned employees do not match the expected employees.",
        )
