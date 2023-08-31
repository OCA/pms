# Copyright 2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import SavepointCase


class PMSTestCommons(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(PMSTestCommons, cls).setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.online_channel = cls.env.ref("pms_website_sale.online_channel")
        cls.demo_partner = cls.env.ref("base.partner_demo")
        cls.public_partner = cls.env.ref("base.public_partner")
        cls.wire_transfer_acquirer = cls.env.ref("payment.payment_acquirer_transfer")

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

        cls.room_1_1 = cls.env["pms.room"].create(
            {
                "name": "room 1/1",
                "room_type_id": cls.room_type_1.id,
                "short_name": "R11",
            }
        )
        cls.room_1_2 = cls.env["pms.room"].create(
            {
                "name": "room 1/2",
                "room_type_id": cls.room_type_1.id,
                "short_name": "R12",
            }
        )
        cls.room_2_1 = cls.env["pms.room"].create(
            {
                "name": "room 2/1",
                "room_type_id": cls.room_type_2.id,
                "short_name": "R21",
            }
        )
        cls.room_2_2 = cls.env["pms.room"].create(
            {
                "name": "room 2/2",
                "room_type_id": cls.room_type_2.id,
                "short_name": "R22",
            }
        )
