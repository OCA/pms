from odoo.tests import common


class TestPms(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.availability_plan1 = self.env["pms.availability.plan"].create(
            {
                "name": "Availability Plan 1",
            }
        )
        self.pricelist1 = self.env["product.pricelist"].create(
            {
                "name": "Pricelist 1",
                "availability_plan_id": self.availability_plan1.id,
                "is_pms_available": True,
            }
        )
        self.company1 = self.env["res.company"].create(
            {
                "name": "Company 1",
            }
        )
        self.pms_property1 = self.env["pms.property"].create(
            {
                "name": "Property 1",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
                "institution_property_id": "Dummy institution property id 1",
            }
        )
        self.pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
                "institution_property_id": "Dummy institution property id 2",
            }
        )
        self.room_type_class1 = self.env["pms.room.type.class"].create(
            {
                "name": "Room Type Class 1",
                "default_code": "RTC1",
            }
        )
