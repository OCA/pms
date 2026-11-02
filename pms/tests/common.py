from odoo.tests import common

INVALID_HOURS = [
    "8:00",
    "8:0",
    "1400",
    "14:00:00",
    "24:00",
    "14:99",
    "aa:bb",
    "14:",
]


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

    def create_pricelist_by_property_scenario(self):
        """
        - create pms_property2 in company1, with room_type_property2
          and one room of it
        - create pricelist_property1 and pricelist_property2, each one
          restricted to its property; pricelist_property2 is the default
          pricelist of pms_property2
        - create partner_pricelist_property1 with pricelist_property1
          as its pricelist
        """
        self.pms_property2 = self.env["pms.property"].create(
            {
                "name": "Property 2",
                "company_id": self.company1.id,
                "default_pricelist_id": self.pricelist1.id,
            }
        )
        self.pricelist_property1 = self.env["product.pricelist"].create(
            {
                "name": "Pricelist Property 1",
                "is_pms_available": True,
                "availability_plan_id": self.availability_plan1.id,
                "pms_property_ids": [(6, 0, [self.pms_property1.id])],
            }
        )
        self.pricelist_property2 = self.env["product.pricelist"].create(
            {
                "name": "Pricelist Property 2",
                "is_pms_available": True,
                "availability_plan_id": self.availability_plan1.id,
                "pms_property_ids": [(6, 0, [self.pms_property2.id])],
            }
        )
        self.pms_property2.default_pricelist_id = self.pricelist_property2
        self.partner_pricelist_property1 = self.env["res.partner"].create(
            {
                "name": "Partner Pricelist Property 1",
                "property_product_pricelist": self.pricelist_property1.id,
            }
        )
        self.room_type_property2 = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property2.id],
                "name": "Double Property 2",
                "default_code": "DBL_P2",
                "class_id": self.room_type_class1.id,
                "list_price": 25,
            }
        )
        self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property2.id,
                "name": "Double 201",
                "room_type_id": self.room_type_property2.id,
                "capacity": 2,
            }
        )
