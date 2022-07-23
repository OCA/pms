import datetime

from freezegun import freeze_time

from .common import TestPms


@freeze_time("2021-02-01")
class TestWizardTravellerReport(TestPms):
    def setUp(self):
        super().setUp()
        self.sale_channel_direct1 = self.env["pms.sale.channel"].create(
            {
                "name": "Door",
                "channel_type": "direct",
            }
        )

        # number of seats established in the property
        self.pms_property1.ine_seats = 50

        # create room types
        self.room_type = self.env["pms.room.type"].create(
            {
                "name": "Room type test",
                "default_code": "DBL_Test",
                "class_id": self.room_type_class1.id,
            }
        )
        # room property 1
        self.room_double_1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Room test 1",
                "room_type_id": self.room_type.id,
                "capacity": 2,
            }
        )

        # room property 2
        self.room_double_property_2 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property2.id,
                "name": "Room test, property 2",
                "room_type_id": self.room_type.id,
                "capacity": 2,
            }
        )

        # create document category
        self.id_category_passport = self.env["res.partner.id_category"].create(
            {
                "name": "Passport",
                "code": "P",
                "active": True,
            }
        )
        self.country_italy = self.env["res.country"].search([("code", "=", "IT")])
        self.country_italy.ensure_one()
        # Create partner for property 1
        self.partner_1 = self.env["res.partner"].create(
            {
                "name": "partner1",
                "country_id": self.country_italy.id,
                "nationality_id": self.country_italy.id,
                "residence_country_id": self.country_italy.id,
                "birthdate_date": "2000-06-25",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category_passport.id,
                "name": "55103354T",
                "valid_from": datetime.date.today(),
                "partner_id": self.partner_1.id,
            }
        )

        # Create partner for property 2
        self.partner_2 = self.env["res.partner"].create(
            {
                "name": "partner2",
                "country_id": self.country_italy.id,
                "nationality_id": self.country_italy.id,
                "residence_country_id": self.country_italy.id,
                "birthdate_date": "2000-06-25",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category_passport.id,
                "name": "45437298Q",
                "valid_from": datetime.date.today(),
                "partner_id": self.partner_2.id,
            }
        )

    def test_checkin_property_not_found(self):
        """
        Checking partners are only generated for the property that corresponds to it.
        Reservation 1: property 1 with its checkin partner
        Reservation 2: proprerty 2 with its checkin partner
        Document number of checkin 2 shouldnt be present at result
        """

        # ARRANGE
        # Create reservation 1
        self.reservation_1 = self.env["pms.reservation"].create(
            {
                "checkin": datetime.date.today(),
                "checkout": datetime.date.today() + datetime.timedelta(days=1),
                "preferred_room_id": self.room_double_1.id,
                "partner_id": self.partner_1.id,
                "adults": 1,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        self.checkin1 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.partner_1.id,
                "reservation_id": self.reservation_1.id,
                "firstname": "John",
                "lastname": "Doe",
            }
        )
        # Create reservation 2
        self.reservation_2 = self.env["pms.reservation"].create(
            {
                "checkin": datetime.date.today(),
                "checkout": datetime.date.today() + datetime.timedelta(days=1),
                "preferred_room_id": self.room_double_property_2.id,
                "partner_id": self.partner_2.id,
                "adults": 1,
                "pms_property_id": self.pms_property2.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        self.checkin2 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.partner_2.id,
                "reservation_id": self.reservation_2.id,
                "firstname": "Martha",
                "lastname": "Stewart",
            }
        )
        # checkin partners on board
        self.checkin1.action_on_board()
        self.checkin2.action_on_board()

        # ACT
        result_checkin_list = (
            self.env["traveller.report.wizard"]
            .create({})
            .generate_checkin_list(self.pms_property1.id)
        )

        # ASSERT
        self.assertNotIn(self.checkin2.document_number, result_checkin_list)

    def test_checkin_property_found(self):
        """
        Checking partners are only generated for the property that corresponds to it.
        Reservation 1: property 1 with its checkin partner
        Reservation 2: proprerty 2 with its checkin partner
        Document number of checkin 1 should be present at result
        """

        # ARRANGE
        # Create reservation 1
        self.reservation_1 = self.env["pms.reservation"].create(
            {
                "checkin": datetime.date.today(),
                "checkout": datetime.date.today() + datetime.timedelta(days=1),
                "preferred_room_id": self.room_double_1.id,
                "partner_id": self.partner_1.id,
                "adults": 1,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        self.checkin1 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.partner_1.id,
                "reservation_id": self.reservation_1.id,
                "firstname": "John",
                "lastname": "Doe",
                "nationality_id": self.country_italy.id,
            }
        )
        # Create reservation 2
        self.reservation_2 = self.env["pms.reservation"].create(
            {
                "checkin": datetime.date.today(),
                "checkout": datetime.date.today() + datetime.timedelta(days=1),
                "preferred_room_id": self.room_double_property_2.id,
                "partner_id": self.partner_2.id,
                "adults": 1,
                "pms_property_id": self.pms_property2.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        self.checkin2 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.partner_2.id,
                "reservation_id": self.reservation_2.id,
                "firstname": "Martha",
                "lastname": "Stewart",
            }
        )
        # checkin partners on board
        self.checkin1.action_on_board()
        self.checkin2.action_on_board()

        # ACT
        result_checkin_list = (
            self.env["traveller.report.wizard"]
            .create({})
            .generate_checkin_list(self.pms_property1.id)
        )

        # ASSERT
        self.assertIn(self.checkin1.document_number, result_checkin_list)
