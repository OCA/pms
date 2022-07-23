import datetime

from freezegun import freeze_time

from odoo.exceptions import ValidationError

from .common import TestPms


@freeze_time("2021-02-01")
class TestWizardINE(TestPms):
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
        # create rooms
        self.room_double_1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Room test 1",
                "room_type_id": self.room_type.id,
                "capacity": 2,
            }
        )
        self.room_double_2 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Room test 2",
                "room_type_id": self.room_type.id,
                "capacity": 2,
            }
        )
        self.room_double_3 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Room test 3",
                "room_type_id": self.room_type.id,
                "capacity": 2,
            }
        )
        self.room_single_1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Room test 4",
                "room_type_id": self.room_type.id,
                "capacity": 1,
                "extra_beds_allowed": 1,
            }
        )
        self.room_triple1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Room test 5",
                "room_type_id": self.room_type.id,
                "capacity": 3,
            }
        )
        # room other property
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
        # get records of russia, italy and afghanistan
        self.country_russia = self.env["res.country"].search([("code", "=", "RU")])
        self.country_russia.ensure_one()
        self.country_italy = self.env["res.country"].search([("code", "=", "IT")])
        self.country_italy.ensure_one()
        self.country_afghanistan = self.env["res.country"].search([("code", "=", "AF")])
        self.country_afghanistan.ensure_one()

    def ideal_scenario(self):
        # Create partner 1 (italy)
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

        # Create partner 2 (russia)
        self.partner_2 = self.env["res.partner"].create(
            {
                "name": "partner2",
                "country_id": self.country_russia.id,
                "nationality_id": self.country_russia.id,
                "residence_country_id": self.country_russia.id,
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
        # Create partner 3 (italy)
        self.partner_3 = self.env["res.partner"].create(
            {
                "name": "partner3",
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
                "name": "81534086Y",
                "valid_from": datetime.date.today(),
                "partner_id": self.partner_3.id,
            }
        )
        # Create partner 4 (italy)
        self.partner_4 = self.env["res.partner"].create(
            {
                "name": "partner4",
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
                "name": "00807643K",
                "valid_from": datetime.date.today(),
                "partner_id": self.partner_4.id,
            }
        )
        # Create partner 5 (afghanistan)
        self.partner_5 = self.env["res.partner"].create(
            {
                "name": "partner5",
                "country_id": self.country_afghanistan.id,
                "nationality_id": self.country_afghanistan.id,
                "residence_country_id": self.country_afghanistan.id,
                "birthdate_date": "2000-06-25",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category_passport.id,
                "name": "54564399G",
                "valid_from": datetime.date.today(),
                "partner_id": self.partner_5.id,
            }
        )
        # Create partner 6 (afghanistan)
        self.partner_6 = self.env["res.partner"].create(
            {
                "name": "partner6",
                "country_id": self.country_afghanistan.id,
                "nationality_id": self.country_afghanistan.id,
                "residence_country_id": self.country_afghanistan.id,
                "birthdate_date": "2000-06-25",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category_passport.id,
                "name": "39854152M",
                "valid_from": datetime.date.today(),
                "partner_id": self.partner_6.id,
            }
        )
        # Create partner 7 (afghanistan)
        self.partner_7 = self.env["res.partner"].create(
            {
                "name": "partner7",
                "country_id": self.country_afghanistan.id,
                "nationality_id": self.country_afghanistan.id,
                "residence_country_id": self.country_afghanistan.id,
                "birthdate_date": "2000-06-25",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category_passport.id,
                "name": "39854152O",
                "valid_from": datetime.date.today(),
                "partner_id": self.partner_7.id,
            }
        )

        # Create reservation 1
        self.reservation_1 = self.env["pms.reservation"].create(
            {
                "checkin": datetime.date.today(),
                "checkout": datetime.date.today() + datetime.timedelta(days=1),
                "preferred_room_id": self.room_double_1.id,
                "partner_id": self.partner_1.id,
                "adults": 2,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        self.checkin1 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.partner_1.id,
                "reservation_id": self.reservation_1.id,
            }
        )

        self.checkin2 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.partner_2.id,
                "reservation_id": self.reservation_1.id,
            }
        )
        # Create reservation 2
        self.reservation_2 = self.env["pms.reservation"].create(
            {
                "checkin": datetime.date.today() + datetime.timedelta(days=1),
                "checkout": datetime.date.today() + datetime.timedelta(days=2),
                "preferred_room_id": self.room_triple1.id,
                "partner_id": self.partner_3.id,
                "adults": 2,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        self.checkin3 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.partner_3.id,
                "reservation_id": self.reservation_2.id,
            }
        )
        self.checkin4 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.partner_4.id,
                "reservation_id": self.reservation_2.id,
            }
        )
        # Create reservation 3
        self.reservation_3 = self.env["pms.reservation"].create(
            {
                "checkin": datetime.date.today() + datetime.timedelta(days=1),
                "checkout": datetime.date.today() + datetime.timedelta(days=3),
                "preferred_room_id": self.room_double_2.id,
                "partner_id": self.partner_5.id,
                "adults": 1,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        self.checkin5 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.partner_5.id,
                "reservation_id": self.reservation_3.id,
            }
        )
        # Create reservation property 2
        self.reservation_property_2 = self.env["pms.reservation"].create(
            {
                "checkin": datetime.date.today() + datetime.timedelta(days=1),
                "checkout": datetime.date.today() + datetime.timedelta(days=3),
                "preferred_room_id": self.room_double_property_2.id,
                "partner_id": self.partner_5.id,
                "adults": 1,
                "pms_property_id": self.pms_property2.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        self.checkin5_other_property = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.partner_5.id,
                "reservation_id": self.reservation_property_2.id,
            }
        )

        # Create extra bed service
        product_extra_bed = self.env["product.product"].create(
            {
                "name": "Product test",
                "is_extra_bed": True,
                "consumed_on": "before",
                "per_day": True,
            }
        )
        vals_service_extra_bed = {
            "is_board_service": False,
            "product_id": product_extra_bed.id,
        }
        # Create reservation 4
        self.reservation_4 = self.env["pms.reservation"].create(
            {
                "checkin": datetime.date.today() + datetime.timedelta(days=1),
                "checkout": datetime.date.today() + datetime.timedelta(days=3),
                "preferred_room_id": self.room_single_1.id,
                "partner_id": self.partner_6.id,
                "adults": 2,
                "pms_property_id": self.pms_property1.id,
                "service_ids": [(0, 0, vals_service_extra_bed)],
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        self.checkin6 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.partner_6.id,
                "reservation_id": self.reservation_4.id,
            }
        )

        self.checkin7 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.partner_7.id,
                "reservation_id": self.reservation_4.id,
            }
        )
        # checkin partners on board
        self.checkin1.action_on_board()
        self.checkin2.action_on_board()
        with freeze_time("2021-02-02"):
            self.checkin3.action_on_board()
            self.checkin4.action_on_board()
            self.checkin5.action_on_board()
            self.checkin6.action_on_board()
            self.checkin7.action_on_board()

        # set prices for nights
        self.reservation_1.reservation_line_ids[0].price = 25.0
        self.reservation_2.reservation_line_ids[0].price = 21.0
        self.reservation_3.reservation_line_ids[0].price = 25.0
        self.reservation_3.reservation_line_ids[1].price = 25.0
        self.reservation_4.reservation_line_ids[0].price = 21.50
        self.reservation_4.reservation_line_ids[1].price = 21.50

    def pending_checkins_scenario(self):
        # Create 3 checkin partners from russia
        self.partner_russia_1 = self.env["res.partner"].create(
            {
                "name": "partner1",
                "country_id": self.country_russia.id,
                "nationality_id": self.country_russia.id,
                "residence_country_id": self.country_russia.id,
                "birthdate_date": "2000-06-25",
                "gender": "male",
            }
        )
        self.partner_russia_2 = self.env["res.partner"].create(
            {
                "name": "partner2",
                "country_id": self.country_russia.id,
                "nationality_id": self.country_russia.id,
                "residence_country_id": self.country_russia.id,
                "birthdate_date": "2000-06-25",
                "gender": "male",
            }
        )
        self.partner_russia_3 = self.env["res.partner"].create(
            {
                "name": "partner3",
                "country_id": self.country_russia.id,
                "nationality_id": self.country_russia.id,
                "residence_country_id": self.country_russia.id,
                "birthdate_date": "2000-06-25",
                "gender": "male",
            }
        )
        # Create document for 3 checkin partners (russia)
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category_passport.id,
                "name": "15103354T",
                "valid_from": datetime.date.today(),
                "partner_id": self.partner_russia_1.id,
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category_passport.id,
                "name": "25103354T",
                "valid_from": datetime.date.today(),
                "partner_id": self.partner_russia_2.id,
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category_passport.id,
                "name": "35103354T",
                "valid_from": datetime.date.today(),
                "partner_id": self.partner_russia_3.id,
            }
        )

        # Create 3 reservations
        self.reservation_1 = self.env["pms.reservation"].create(
            {
                "checkin": datetime.date.today(),
                "checkout": datetime.date.today() + datetime.timedelta(days=1),
                "preferred_room_id": self.room_double_1.id,
                "partner_id": self.partner_russia_1.id,
                "adults": 2,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        self.reservation_2 = self.env["pms.reservation"].create(
            {
                "checkin": datetime.date.today() + datetime.timedelta(days=1),
                "checkout": datetime.date.today() + datetime.timedelta(days=2),
                "preferred_room_id": self.room_double_2.id,
                "partner_id": self.partner_russia_2.id,
                "adults": 2,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        self.reservation_3 = self.env["pms.reservation"].create(
            {
                "checkin": datetime.date.today() + datetime.timedelta(days=1),
                "checkout": datetime.date.today() + datetime.timedelta(days=3),
                "preferred_room_id": self.room_double_3.id,
                "partner_id": self.partner_russia_3.id,
                "adults": 2,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # Create 3 checkin partners (1 russian -> r1, 2 russian -> r3 )
        self.checkin_partner_r1_1 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.partner_russia_1.id,
                "reservation_id": self.reservation_1.id,
            }
        )
        self.checkin_partner_r3_1 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.partner_russia_2.id,
                "reservation_id": self.reservation_3.id,
            }
        )
        self.checkin_partner_r3_2 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.partner_russia_3.id,
                "reservation_id": self.reservation_3.id,
            }
        )
        # checkin partners on board
        self.checkin_partner_r1_1.action_on_board()
        with freeze_time("2021-02-02"):
            self.checkin_partner_r3_1.action_on_board()
            self.checkin_partner_r3_2.action_on_board()

    def test_room_type_num_by_date(self):
        """
        +============================+==============+==============+=============+
        |                            |      01      |      02      |     03      |
        +============================+==============+==============+=============+
        | r1  2 adults               | DOUBLE ROOM  |              |             |
        | r2  2 adults               |              | TRIPLE ROOM  |             |
        | r3  1 adult                |              | DOUBLE ROOM  | DOUBLE ROOM |
        | r4  2 adults (1 extra bed) |              | SINGLE ROOM  | SINGLE ROOM |
        +============================+==============+==============+=============+
        | double rooms (use double)  |      1       |      0       |      0      |
        +============================+==============+==============+=============+
        | double rooms (use single)  |      0       |      1       |      1      |
        +============================+==============+==============+=============+
        | other rooms                |      0       |      2       |      1      |
        +============================+==============+==============+=============+
        | extra beds                 |      0       |      1       |      1      |
        +============================+==============+==============+=============+
        """
        # ARRANGE
        self.ideal_scenario()
        start_date = datetime.date(2021, 2, 1)
        second_date = datetime.date(2021, 2, 2)
        end_date = datetime.date(2021, 2, 3)

        expected_result = {
            start_date: {
                "double_rooms_double_use": 1,
                "double_rooms_single_use": 0,
                "other_rooms": 0,
                "extra_beds": 0,
            },
            second_date: {
                "double_rooms_double_use": 0,
                "double_rooms_single_use": 1,
                "other_rooms": 2,
                "extra_beds": 1,
            },
            end_date: {
                "double_rooms_double_use": 0,
                "double_rooms_single_use": 1,
                "other_rooms": 1,
                "extra_beds": 1,
            },
        }

        # ACT
        rooms = self.env["pms.ine.wizard"].ine_rooms(
            start_date, end_date, self.pms_property1
        )
        # ASSERT
        self.assertDictEqual(rooms, expected_result)

    def test_arrivals_departures_pernoctations_by_date(self):
        """
        +===========================+==============+==============+=============+=============+
        |                           |      01      |      02      |     03      |   04        |
        +===========================+==============+==============+=============+=============+
        | r1  2 adults              | italy,russia | italy,russia |             |             |
        +---------------------------+--------------+--------------+-------------+-------------+
        | r2  2 adults              |              | italy,italy  | italy,italy |             |
        +---------------------------+--------------+--------------+-------------+-------------+
        | r3  1 adult               |              | afghanistan  | afghanistan | afghanistan |
        +---------------------------+--------------+--------------+-------------+-------------+
        | r4  2 adults              |              | afghanistan  | afghanistan | afghanistan |
        |                           |              | afghanistan  | afghanistan | afghanistan |
        +===========================+==============+==============+=============+=============+
        | arrivals  Afghanistan     |              | 3            |             |             |
        | arrivals  Italy           | 1            | 2            |             |             |
        | arrivals  Russia          | 1            |              |             |             |
        +===========================+==============+==============+=============+=============+
        | pernoctations Afghanistan |              | 3            | 3           |             |
        | pernoctations Italy       | 1            | 2            |             |             |
        | pernoctations Russia      | 1            |              |             |             |
        +===========================+==============+==============+=============+=============+
        | departures Afghanistan    |              |              |             | 3           |
        | departures Italy          |              | 1            | 2           |             |
        | departures Russia         |              | 1            |             |             |
        +===========================+==============+==============+=============+=============+
        """
        # ARRANGE
        self.ideal_scenario()
        start_date = datetime.date(2021, 2, 1)
        second_date = datetime.date(2021, 2, 2)
        third_date = datetime.date(2021, 2, 3)
        end_date = datetime.date(2021, 2, 4)

        expected_result = {
            self.country_italy.code: {
                start_date: {
                    "arrivals": 1,
                    "pernoctations": 1,
                },
                second_date: {
                    "arrivals": 2,
                    "pernoctations": 2,
                    "departures": 1,
                },
                third_date: {
                    "departures": 2,
                },
            },
            self.country_russia.code: {
                start_date: {
                    "arrivals": 1,
                    "pernoctations": 1,
                },
                second_date: {
                    "departures": 1,
                },
            },
            self.country_afghanistan.code: {
                second_date: {
                    "arrivals": 3,
                    "pernoctations": 3,
                },
                third_date: {
                    "pernoctations": 3,
                },
                end_date: {
                    "departures": 3,
                },
            },
        }
        # ACT
        nationalities = self.env["pms.ine.wizard"].ine_nationalities(
            start_date, end_date, self.pms_property1.id
        )
        # ASSERT
        self.assertDictEqual(nationalities, expected_result)

    def test_spain_arrivals_departures_pernoctations_by_date(self):
        """
        +==========================+============+============+=========+========+
        |                          |     01     |     02     |   03    |   04   |
        +==========================+============+============+=========+========+
        | r1  2 adults             | Ourense    | Ourense    |         |        |
        |                          | Pontevedra | Pontevedra |         |        |
        +--------------------------+------------+------------+---------+--------+
        | r2  2 adults             |            | Ourense    | Ourense |        |
        |                          |            | Ourense    | Ourense |        |
        +--------------------------+------------+------------+---------+--------+
        | r3  1 adult              |            | Madrid     | Madrid  | Madrid |
        +--------------------------+------------+------------+---------+--------+
        | r4  2 adults             |            | Madrid     | Madrid  | Madrid |
        |                          |            | Madrid     | Madrid  | Madrid |
        +==========================+============+============+=========+========+
        | arrivals  Madrid         |            | 3          |         |        |
        | arrivals  Ourense        | 1          | 2          |         |        |
        | arrivals  Pontevedra     | 1          |            |         |        |
        +==========================+============+============+=========+========+
        | pernoctations Madrid     |            | 3          | 3       |        |
        | pernoctations Ourense    | 1          | 2          |         |        |
        | pernoctations Pontevedra | 1          |            |         |        |
        0+=========================+============+============+=========+========+
        | departures Madrid        |            |            |         | 3      |
        | departures Ourense       |            | 1          | 2       |        |
        | departures Pontevedra    |            | 1          |         |        |
        +==========================+============+============+=========+========+
        """
        # ARRANGE
        self.ideal_scenario()
        start_date = datetime.date(2021, 2, 1)
        second_date = datetime.date(2021, 2, 2)
        third_date = datetime.date(2021, 2, 3)
        end_date = datetime.date(2021, 2, 4)

        country_spain = self.env["res.country"].search([("code", "=", "ES")])
        state_madrid = self.env["res.country.state"].search([("name", "=", "Madrid")])
        state_ourense = self.env["res.country.state"].search(
            [("name", "=", "Ourense (Orense)")]
        )
        state_pontevedra = self.env["res.country.state"].search(
            [("name", "=", "Pontevedra")]
        )

        self.checkin1.nationality_id = country_spain
        self.partner_1.nationality_id = country_spain
        self.checkin1.residence_state_id = state_ourense
        self.partner_1.residence_state_id = state_ourense

        self.checkin2.nationality_id = country_spain
        self.partner_2.nationality_id = country_spain
        self.checkin2.residence_state_id = state_pontevedra
        self.partner_2.residence_state_id = state_pontevedra

        self.checkin3.nationality_id = country_spain
        self.partner_3.nationality_id = country_spain
        self.checkin3.residence_state_id = state_ourense
        self.partner_3.residence_state_id = state_ourense

        self.checkin4.nationality_id = country_spain
        self.partner_4.nationality_id = country_spain
        self.checkin4.residence_state_id = state_ourense
        self.partner_4.residence_state_id = state_ourense

        self.checkin5.nationality_id = country_spain
        self.partner_5.nationality_id = country_spain
        self.checkin5.residence_state_id = state_madrid
        self.partner_5.residence_state_id = state_madrid

        self.checkin6.nationality_id = country_spain
        self.partner_6.nationality_id = country_spain
        self.checkin6.residence_state_id = state_madrid
        self.partner_6.residence_state_id = state_madrid

        self.checkin7.nationality_id = country_spain
        self.partner_7.nationality_id = country_spain
        self.checkin7.residence_state_id = state_madrid
        self.partner_7.residence_state_id = state_madrid

        expected_result = {
            country_spain.code: {
                state_madrid.ine_code: {
                    second_date: {
                        "arrivals": 3,
                        "pernoctations": 3,
                    },
                    third_date: {
                        "pernoctations": 3,
                    },
                    end_date: {
                        "departures": 3,
                    },
                },
                state_ourense.ine_code: {
                    start_date: {
                        "arrivals": 1,
                        "pernoctations": 1,
                    },
                    second_date: {
                        "arrivals": 2,
                        "pernoctations": 2,
                        "departures": 1,
                    },
                    third_date: {
                        "departures": 2,
                    },
                },
                state_pontevedra.ine_code: {
                    start_date: {
                        "arrivals": 1,
                        "pernoctations": 1,
                    },
                    second_date: {
                        "departures": 1,
                    },
                },
            }
        }
        # ACT
        nationalities = self.env["pms.ine.wizard"].ine_nationalities(
            start_date, end_date, self.pms_property1.id
        )
        # ASSERT
        self.assertDictEqual(nationalities, expected_result)

    def test_calculate_monthly_adr(self):
        """
        +-------------+-------+-------+-------+
        |             |  01   |  02   |  03   |
        +-------------+-------+-------+-------+
        | r1          | 25.00 |       |       |
        | r2          |       | 21.00 |       |
        | r3          |       | 25.00 | 25.00 |
        | r4          |       | 21.50 | 21.50 |
        +-------------+-------+-------+-------+
        | adr         | 25.00 | 22.50 | 23.25 |
        +-------------+-------+-------+-------+
        | monthly adr |        23.58          |
        +-------------+-------+-------+-------+
        """
        # ARRANGE
        self.ideal_scenario()
        start_date = datetime.date(2021, 2, 1)
        end_date = datetime.date(2021, 2, 28)
        expected_monthly_adr = 23.58

        # ACT
        wizard = self.env["pms.ine.wizard"].new(
            {
                "pms_property_id": self.pms_property1.id,
                "start_date": start_date,
                "end_date": end_date,
            }
        )

        monthly_adr = wizard.ine_calculate_adr(start_date, end_date)
        # ASSERT
        self.assertEqual(
            expected_monthly_adr,
            monthly_adr,
        )

    def test_calculate_monthly_revpar(self):
        """
        +----------------+-------+-------+-------+
        |                |  01   |  02   |  03   |
        +----------------+-------+-------+-------+
        | r1             | 25.00 |       |       |
        | r2             |       | 21.00 |       |
        | r3             |       | 25.00 | 25.00 |
        | r4             |       | 21.50 | 21.50 |
        +----------------+-------+-------+-------+
        | monthly revpar |        23.58          |
        +----------------+-------+-------+-------+
        num rooms avail = 5
        income = 25.00 + 21.00 + 25.00 + 25.00 + 21.50 + 21.50 = 139
        monthly revpar = 139 / (5 * 28) = 0.99
        """
        # ARRANGE
        self.ideal_scenario()
        start_date = datetime.date(2021, 2, 1)
        end_date = datetime.date(2021, 2, 28)
        expected_monthly_revpar = 0.99

        # ACT
        wizard = self.env["pms.ine.wizard"].new(
            {
                "pms_property_id": self.pms_property1.id,
                "start_date": start_date,
                "end_date": end_date,
            }
        )
        monthly_revpar = wizard.ine_calculate_revpar(start_date, end_date)
        # ASSERT
        self.assertEqual(
            expected_monthly_revpar,
            monthly_revpar,
        )

    def test_arrivals_departures_pernoctations_by_date_pending_checkins(self):
        """
        if unknown checkin =>  Madrid
        +==========================+============+============+=========+========+
        |                          |     01     |     02     |   03    |   04   |
        +==========================+============+============+=========+========+
        | r1  2 adults             | Russia     | Russia     |         |        |
        |                          | unknown    | unknown    |         |        |
        +--------------------------+------------+------------+---------+--------+
        | r2  2 adults             |            | unknown    | unknown |        |
        |                          |            | unknown    | unknown |        |
        +--------------------------+------------+------------+---------+--------+
        | r3  2 adults             |            | Russia     | Russia  | Russia |
        |                          |            | Russia     | Russia  | Russia |
        +==========================+============+============+=========+========+
        | arrivals  Russia         | 2          | 2          |         |        |
        | arrivals  Madrid         |            | 2          |         |        |
        +==========================+============+============+=========+========+
        | pernoctations Russia     | 2          | 2          | 2       |        |
        | pernoctations Madrid     |            | 2          |         |        |
        0+=========================+============+============+=========+========+
        | departures Russia        |            | 2          |         | 2      |
        | departures Madrid        |            |            | 2       |        |
        +==========================+============+============+=========+========+
        """
        # ARRANGE
        self.pending_checkins_scenario()
        start_date = datetime.date(2021, 2, 1)
        second_date = datetime.date(2021, 2, 2)
        third_date = datetime.date(2021, 2, 3)
        end_date = datetime.date(2021, 2, 4)

        expected_result = {
            self.country_russia.code: {
                start_date: {
                    "arrivals": 1,
                    "pernoctations": 1,
                },
                second_date: {
                    "arrivals": 2,
                    "pernoctations": 2,
                    "departures": 1,
                },
                third_date: {
                    "pernoctations": 2,
                },
                end_date: {
                    "departures": 2,
                },
            },
        }
        # ACT
        nationalities = self.env["pms.ine.wizard"].ine_nationalities(
            start_date, end_date, self.pms_property1.id
        )
        # ASSERT
        self.assertDictEqual(nationalities, expected_result)

    def test_arrivals_departures_pernoctations_by_date_no_nationality_raises_error(
        self,
    ):
        """
        +===========================+==============+==============+=============+=============+
        |                           |      01      |      02      |     03      |   04        |
        +===========================+==============+==============+=============+=============+
        | r1  2 adults              | italy, False | italy, False |             |             |
        +---------------------------+--------------+--------------+-------------+-------------+
        | r2  2 adults              |              | italy,italy  | italy,italy |             |
        +---------------------------+--------------+--------------+-------------+-------------+
        | r3  1 adult               |              | afghanistan  | afghanistan | afghanistan |
        +---------------------------+--------------+--------------+-------------+-------------+
        | r4  2 adults              |              | afghanistan  | afghanistan | afghanistan |
        |                           |              | afghanistan  | afghanistan | afghanistan |
        +===========================+==============+==============+=============+=============+
        | arrivals  Afghanistan     |              | 3            |             |             |
        | arrivals  Italy           | 1            | 2            |             |             |
        | arrivals  Russia          | 1            |              |             |             |
        +===========================+==============+==============+=============+=============+
        | pernoctations Afghanistan |              | 3            | 3           |             |
        | pernoctations Italy       | 1            | 2            |             |             |
        | pernoctations Russia      | 1            |              |             |             |
        +===========================+==============+==============+=============+=============+
        | departures Afghanistan    |              |              |             | 3           |
        | departures Italy          |              | 1            | 2           |             |
        | departures Russia         |              | 1            |             |             |
        +===========================+==============+==============+=============+=============+
        """
        # ARRANGE
        self.ideal_scenario()
        self.reservation_1.checkin_partner_ids[1].nationality_id = False
        start_date = datetime.date(2021, 2, 1)
        end_date = datetime.date(2021, 2, 4)

        # ACT & ASSERT
        with self.assertRaises(
            ValidationError,
            msg="Cannot generate INE if some checkin partner has no nationality",
        ):
            self.env["pms.ine.wizard"].ine_nationalities(
                start_date, end_date, self.pms_property1.id
            )

    def test_spain_arrivals_departures_pernoctations_by_date_no_state_raises_error(
        self,
    ):
        """
        +==========================+============+============+=========+========+
        |                          |     01     |     02     |   03    |   04   |
        +==========================+============+============+=========+========+
        | r1  2 adults             | Ourense    | Ourense    |         |        |
        |                          | False      | False      |         |        |
        +--------------------------+------------+------------+---------+--------+
        | r2  2 adults             |            | Ourense    | Ourense |        |
        |                          |            | Ourense    | Ourense |        |
        +--------------------------+------------+------------+---------+--------+
        | r3  1 adult              |            | Madrid     | Madrid  | Madrid |
        +--------------------------+------------+------------+---------+--------+
        | r4  2 adults             |            | Madrid     | Madrid  | Madrid |
        |                          |            | Madrid     | Madrid  | Madrid |
        +==========================+============+============+=========+========+
        | arrivals  Madrid         |            | 3          |         |        |
        | arrivals  Ourense        | 1          | 2          |         |        |
        | arrivals  Pontevedra     | 1          |            |         |        |
        +==========================+============+============+=========+========+
        | pernoctations Madrid     |            | 3          | 3       |        |
        | pernoctations Ourense    | 1          | 2          |         |        |
        | pernoctations Pontevedra | 1          |            |         |        |
        0+=========================+============+============+=========+========+
        | departures Madrid        |            |            |         | 3      |
        | departures Ourense       |            | 1          | 2       |        |
        | departures Pontevedra    |            | 1          |         |        |
        +==========================+============+============+=========+========+
        """
        # ARRANGE
        self.ideal_scenario()
        start_date = datetime.date(2021, 2, 1)
        end_date = datetime.date(2021, 2, 4)

        country_spain = self.env["res.country"].search([("code", "=", "ES")])
        state_madrid = self.env["res.country.state"].search([("name", "=", "Madrid")])
        state_ourense = self.env["res.country.state"].search(
            [("name", "=", "Ourense (Orense)")]
        )

        self.checkin1.nationality_id = country_spain
        self.partner_1.nationality_id = country_spain
        self.checkin1.residence_state_id = state_ourense
        self.partner_1.residence_state_id = state_ourense

        self.checkin2.nationality_id = country_spain
        self.partner_2.nationality_id = country_spain
        self.checkin2.residence_state_id = False
        self.partner_2.residence_state_id = False

        self.checkin3.nationality_id = country_spain
        self.partner_3.nationality_id = country_spain
        self.checkin3.residence_state_id = state_ourense
        self.partner_3.residence_state_id = state_ourense

        self.checkin4.nationality_id = country_spain
        self.partner_4.nationality_id = country_spain
        self.checkin4.residence_state_id = state_ourense
        self.partner_4.residence_state_id = state_ourense

        self.checkin5.nationality_id = country_spain
        self.partner_5.nationality_id = country_spain
        self.checkin5.residence_state_id = state_madrid
        self.partner_5.residence_state_id = state_madrid

        self.checkin6.nationality_id = country_spain
        self.partner_6.nationality_id = country_spain
        self.checkin6.residence_state_id = state_madrid
        self.partner_6.residence_state_id = state_madrid

        self.checkin7.nationality_id = country_spain
        self.partner_7.nationality_id = country_spain
        self.checkin7.residence_state_id = state_madrid
        self.partner_7.residence_state_id = state_madrid

        # ACT & ASSERT
        with self.assertRaises(
            ValidationError,
            msg="Cannot generate INE if some checkin partner from Spain has no nationality",
        ):
            self.env["pms.ine.wizard"].ine_nationalities(
                start_date, end_date, self.pms_property1.id
            )
