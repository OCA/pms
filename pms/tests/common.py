from odoo.tests import common


class TestPms(common.SavepointCase):
    def setUp(self):
        super().setUp()
        self.pricelist1 = self.env["product.pricelist"].create(
            {
                "name": "Pricelist 1",
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
            }
        )
        self.room_type_class1 = self.env["pms.room.type.class"].create(
            {
                "name": "Room Type Class 1",
                "default_code": "RTC1",
            }
        )
