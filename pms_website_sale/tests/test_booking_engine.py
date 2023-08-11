from odoo.tests.common import SavepointCase

from odoo.addons.pms_website_sale.controllers.main import WebsiteSale


class BookingEngineCase(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(BookingEngineCase, cls).setUpClass()

        cls.ws_controller = WebsiteSale()
        cls.public_user = cls.env.ref("base.public_user")
        cls.company = cls.env.ref("base.main_company")
        cls.online_channel = cls.env.ref("pms_website_sale.online_channel")

        cls.property = cls.env["pms.property"].create(
            {
                "name": "Property Test 1",
                "company_id": cls.company.id,
            }
        )
        cls.room_type_class_1 = cls.env["pms.room.type.class"].create(
            {
                "name": "room type class 1",
                "default_code": "RTC1",
            }
        )
        cls.room_type_1 = cls.env["pms.room.type"].create(
            {
                "name": "room type 1",
                "default_code": "RT1",
                "class_id": cls.room_type_class_1.id,
            }
        )
        cls.room_type_2 = cls.env["pms.room.type"].create(
            {
                "name": "room type 2",
                "default_code": "RT2",
                "class_id": cls.room_type_class_1.id,
            }
        )
        cls.case_room_types = cls.room_type_1 | cls.room_type_2

        cls.room_1 = cls.env["pms.room"].create(
            {
                "name": "room 1",
                "room_type_id": cls.room_type_1.id,
                "short_name": "TES1",
            }
        )
        cls.room_2 = cls.env["pms.room"].create(
            {
                "name": "room 2",
                "room_type_id": cls.room_type_1.id,
                "short_name": "TES2",
            }
        )

    def test_compute_availability_results_with_no_dates(self):
        engine = self.env["pms.booking.engine"].create(
            {
                "pms_property_id": self.property.id,
                "channel_type_id": self.online_channel.id,
            }
        )
        # only consider the rooms created in this case
        availabilities = engine.availability_results.filtered(
            lambda ar: ar.room_type_id in self.case_room_types
        )
        self.assertEqual(len(availabilities), 2)
        self.assertEqual(availabilities.mapped(lambda a: a.num_rooms_available), [0, 0])
