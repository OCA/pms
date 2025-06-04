from odoo.tests import common


class TestPms(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.availability_plan1 = cls.env["pms.availability.plan"].create(
            {"name": "Availability Plan 1"}
        )
        cls.pricelist1 = cls.env["product.pricelist"].create(
            {
                "name": "Pricelist 1",
                "availability_plan_id": cls.availability_plan1.id,
            }
        )
        cls.company1 = cls.env["res.company"].create(
            {
                "name": "Company 1",
            }
        )
        cls.pms_property1 = cls.env["pms.property"].create(
            {
                "name": "Property 1",
                "company_id": cls.company1.id,
                "default_pricelist_id": cls.pricelist1.id,
            }
        )
        cls.room_type_class1 = cls.env["pms.room.type.class"].create(
            {
                "name": "Room Type Class 1",
                "default_code": "RTC1",
            }
        )
        for pricelist in cls.env["product.pricelist"].search([]):
            if not pricelist.availability_plan_id:
                pricelist.availability_plan_id = cls.availability_plan1.id
                pricelist.is_pms_available = True
