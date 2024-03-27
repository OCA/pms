from odoo.tests import common


class TestPms(common.SavepointCase):
    def setUp(self):
        super().setUp()
        # delete all previous pms.housekeeping.task.type records (only for the test purpose)
        self.env["pms.housekeeping.task.type"].search([]).unlink()
        # create a sale channel
        self.sale_channel1 = self.env["pms.sale.channel"].create(
            {
                "name": "Door",
                "channel_type": "direct",
            }
        )
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
            }
        )
        self.room_type_class1 = self.env["pms.room.type.class"].create(
            {
                "name": "Room Type Class 1",
                "default_code": "RTC1",
            }
        )
        self.room_type1 = self.env["pms.room.type"].create(
            {
                "name": "Room type 1",
                "default_code": "c1",
                "company_id": self.company1.id,
                "class_id": self.room_type_class1.id,
            }
        )

        self.room1 = self.env["pms.room"].create(
            {
                "name": "Room 101",
                "pms_property_id": self.pms_property1.id,
                "room_type_id": self.room_type1.id,
            }
        )
        # create partner
        self.partner1 = self.env["res.partner"].create({"name": "Ana"})
