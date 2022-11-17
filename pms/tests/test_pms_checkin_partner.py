import datetime
import logging

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from odoo import fields
from odoo.exceptions import ValidationError

from .common import TestPms

_logger = logging.getLogger(__name__)


class TestPmsCheckinPartner(TestPms):
    @freeze_time("2012-01-14")
    def setUp(self):
        super().setUp()
        self.room_type1 = self.env["pms.room.type"].create(
            {
                "pms_property_ids": [self.pms_property1.id],
                "name": "Triple",
                "default_code": "TRP",
                "class_id": self.room_type_class1.id,
            }
        )
        self.room1 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Triple 101",
                "room_type_id": self.room_type1.id,
                "capacity": 3,
            }
        )
        self.room1_2 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Triple 111",
                "room_type_id": self.room_type1.id,
                "capacity": 3,
            }
        )
        self.room1_3 = self.env["pms.room"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "name": "Triple 222",
                "room_type_id": self.room_type1.id,
                "capacity": 3,
            }
        )

        self.host1 = self.env["res.partner"].create(
            {
                "name": "Miguel",
                "email": "miguel@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        self.id_category = self.env["res.partner.id_category"].search(
            [("code", "=", "D")]
        )
        if not self.id_category:
            self.id_category = self.env["res.partner.id_category"].create(
                {"name": "DNI", "code": "D"}
            )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "30065089H",
                "valid_from": datetime.date.today(),
                "partner_id": self.host1.id,
            }
        )
        self.sale_channel_direct1 = self.env["pms.sale.channel"].create(
            {
                "name": "Door",
                "channel_type": "direct",
            }
        )
        reservation_vals = {
            "checkin": datetime.date.today(),
            "checkout": datetime.date.today() + datetime.timedelta(days=3),
            "room_type_id": self.room_type1.id,
            "partner_id": self.host1.id,
            "adults": 3,
            "pms_property_id": self.pms_property1.id,
            "sale_channel_origin_id": self.sale_channel_direct1.id,
        }
        self.reservation_1 = self.env["pms.reservation"].create(reservation_vals)
        self.checkin1 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.host1.id,
                "reservation_id": self.reservation_1.id,
            }
        )

    def test_auto_create_checkins(self):
        """
        Check that as many checkin_partners are created as there
        adults on the reservation

        Reservation has three adults
        """

        # ACTION
        checkins_count = len(self.reservation_1.checkin_partner_ids)
        # ASSERT
        self.assertEqual(
            checkins_count,
            3,
            "the automatic partner checkin was not created successful",
        )

    @freeze_time("2012-01-14")
    def test_auto_unlink_checkins(self):
        # ACTION
        host2 = self.env["res.partner"].create(
            {
                "name": "Carlos",
                "mobile": "654667733",
                "email": "carlos@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "85564627G",
                "valid_from": datetime.date.today(),
                "partner_id": host2.id,
            }
        )
        self.reservation_1.checkin_partner_ids = [
            (
                0,
                False,
                {
                    "partner_id": host2.id,
                },
            )
        ]

        checkins_count = len(self.reservation_1.checkin_partner_ids)

        # ASSERT
        self.assertEqual(
            checkins_count,
            3,
            "the automatic partner checkin was not updated successful",
        )

    def test_onboard_checkin(self):
        """
        Check that the reservation cannot be onboard because
        checkin_partner data are incomplete and not have onboard status
        """

        # ACT & ASSERT
        with self.assertRaises(
            ValidationError, msg="Reservation state cannot be 'onboard'"
        ):
            self.reservation_1.state = "onboard"

    @freeze_time("2012-01-14")
    def test_onboard_reservation(self):
        """
        Check that reservation state is onboard as the checkin day is
        today and checkin_partners data are complete
        """
        # ACT
        self.checkin1.action_on_board()

        # ASSERT
        self.assertEqual(
            self.reservation_1.state,
            "onboard",
            "the reservation checkin was not successful",
        )

    @freeze_time("2012-01-14")
    def test_premature_checkin(self):
        """
        Check that cannot change checkin_partner state to onboard if
        it's not yet checkin day
        """

        # ARRANGE
        self.reservation_1.write(
            {
                "checkin": datetime.date.today() + datetime.timedelta(days=1),
            }
        )
        # ACT & ASSERT
        with self.assertRaises(ValidationError, msg="Cannot do checkin onboard"):
            self.checkin1.action_on_board()

    @freeze_time("2012-01-14")
    def test_late_checkin_on_checkout_day(self):
        """
        Check that allowed register checkin arrival the next day
        even if it is the same day of checkout
        """

        # ARRANGE
        self.reservation_1.write(
            {
                "checkin": datetime.date.today() + datetime.timedelta(days=-1),
                "checkout": datetime.date.today(),
            }
        )

        # ACT
        self.checkin1.action_on_board()

        # ASSERT
        self.assertEqual(
            self.checkin1.arrival,
            fields.datetime.now(),
            """The system did not allow to check in the next
            day because it was the same day of checkout""",
        )

    @freeze_time("2012-01-13")
    def test_late_checkin(self):
        """
        When host arrives late anad has already passed the checkin day,
        the arrival date is updated up to that time.

        In this case checkin day was 2012-01-14 and the host arrived a day later
        so the arrival date is updated to that time

        """

        # ARRANGE
        self.reservation_1.write(
            {
                "checkin": datetime.date.today(),
            }
        )

        # ACT
        self.checkin1.action_on_board()

        # ASSERT
        self.assertEqual(
            self.checkin1.arrival,
            fields.datetime.now(),
            "the late checkin has problems",
        )

    @freeze_time("2012-01-14")
    def test_too_many_people_checkin(self):
        """
        Reservation cannot have more checkin_partners than adults who have
        Reservation has three adults and cannot have four checkin_partner
        """

        # ARRANGE
        host2 = self.env["res.partner"].create(
            {
                "name": "Carlos",
                "mobile": "654667733",
                "email": "carlos@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "95876871Z",
                "valid_from": datetime.date.today(),
                "partner_id": host2.id,
            }
        )
        host3 = self.env["res.partner"].create(
            {
                "name": "Enmanuel",
                "mobile": "654667733",
                "email": "enmanuel@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "58261664L",
                "valid_from": datetime.date.today(),
                "partner_id": host3.id,
            }
        )
        host4 = self.env["res.partner"].create(
            {
                "name": "Enrique",
                "mobile": "654667733",
                "email": "enrique@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "61645604S",
                "valid_from": datetime.date.today(),
                "partner_id": host4.id,
            }
        )
        self.env["pms.checkin.partner"].create(
            {
                "partner_id": host2.id,
                "reservation_id": self.reservation_1.id,
            }
        )
        self.env["pms.checkin.partner"].create(
            {
                "partner_id": host3.id,
                "reservation_id": self.reservation_1.id,
            }
        )
        # ACT & ASSERT
        with self.assertRaises(
            ValidationError,
            msg="Reservation cannot have more checkin_partner than adults who have",
        ):
            self.reservation_1.write(
                {
                    "checkin_partner_ids": [
                        (
                            0,
                            0,
                            {
                                "partner_id": host4.id,
                            },
                        )
                    ]
                }
            )

    @freeze_time("2012-01-14")
    def test_count_pending_arrival_persons(self):
        """
        After making onboard of two of the three checkin_partners,
        one must remain pending arrival, that is a ratio of two thirds
        """

        # ARRANGE
        self.host2 = self.env["res.partner"].create(
            {
                "name": "Carlos",
                "mobile": "654667733",
                "email": "carlos@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "63073204M",
                "valid_from": datetime.date.today(),
                "partner_id": self.host2.id,
            }
        )
        self.host3 = self.env["res.partner"].create(
            {
                "name": "Enmanuel",
                "mobile": "654667733",
                "email": "enmanuel@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "70699468K",
                "valid_from": datetime.date.today(),
                "partner_id": self.host3.id,
            }
        )

        self.checkin2 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.host2.id,
                "reservation_id": self.reservation_1.id,
            }
        )
        self.checkin3 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.host3.id,
                "reservation_id": self.reservation_1.id,
            }
        )

        # ACT
        self.checkin1.action_on_board()
        self.checkin2.action_on_board()

        # ASSERT
        self.assertEqual(
            self.reservation_1.count_pending_arrival,
            1,
            "Fail the count pending arrival on reservation",
        )
        self.assertEqual(
            self.reservation_1.checkins_ratio,
            int(2 * 100 / 3),
            "Fail the checkins ratio on reservation",
        )

    def test_complete_checkin_data(self):
        """
        Reservation for three adults in a first place has three checkin_partners
        pending data. Check that there decrease once their data are entered.

        Reservation has three adults, after entering data of two of them,
        check that only one remains to be checked and the ratio of data entered
        from checkin_partners is two thirds
        """

        # ARRANGE
        self.host2 = self.env["res.partner"].create(
            {
                "name": "Carlos",
                "mobile": "654667733",
                "email": "carlos@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "12650631X",
                "valid_from": datetime.date.today(),
                "partner_id": self.host2.id,
            }
        )
        # ACT

        self.checkin2 = self.env["pms.checkin.partner"].create(
            {
                "partner_id": self.host2.id,
                "reservation_id": self.reservation_1.id,
            }
        )
        pending_checkin_data = self.reservation_1.pending_checkin_data
        ratio_checkin_data = self.reservation_1.ratio_checkin_data
        # ASSERT
        self.assertEqual(
            pending_checkin_data,
            1,
            "Fail the count pending checkin data on reservation",
        )
        self.assertEqual(
            ratio_checkin_data,
            int(2 * 100 / 3),
            "Fail the checkins data ratio on reservation",
        )

    @freeze_time("2012-01-14")
    def test_auto_arrival_delayed(self):
        """
        The state of reservation 'arrival_delayed' happen when the checkin day
        has already passed and the resrvation had not yet changed its state to onboard.

        The date that was previously set was 2012-01-14,
        it was advanced two days (to 2012-01-16).
        There are three reservations with checkin day on 2012-01-15,
        after invoking the method auto_arrival_delayed
        those reservation change their state to 'auto_arrival_delayed'
        """

        # ARRANGE
        self.host2 = self.env["res.partner"].create(
            {
                "name": "Carlos",
                "mobile": "654667733",
                "email": "carlos@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "61369791H",
                "valid_from": datetime.date.today(),
                "partner_id": self.host2.id,
            }
        )
        self.host3 = self.env["res.partner"].create(
            {
                "name": "Enmanuel",
                "mobile": "654667733",
                "email": "enmanuel@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "53563260D",
                "valid_from": datetime.date.today(),
                "partner_id": self.host3.id,
            }
        )
        self.host4 = self.env["res.partner"].create(
            {
                "name": "Enrique",
                "mobile": "654667733",
                "email": "enrique@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "63742138F",
                "valid_from": datetime.date.today(),
                "partner_id": self.host4.id,
            }
        )
        self.reservation_1.write(
            {
                "checkin": datetime.date.today() + datetime.timedelta(days=1),
                "checkout": datetime.date.today() + datetime.timedelta(days=6),
                "adults": 1,
            }
        )
        reservation2_vals = {
            "checkin": datetime.date.today() + datetime.timedelta(days=1),
            "checkout": datetime.date.today() + datetime.timedelta(days=6),
            "adults": 1,
            "room_type_id": self.room_type1.id,
            "partner_id": self.host1.id,
            "pms_property_id": self.pms_property1.id,
            "folio_id": self.reservation_1.folio_id.id,
        }
        reservation3_vals = {
            "checkin": datetime.date.today() + datetime.timedelta(days=1),
            "checkout": datetime.date.today() + datetime.timedelta(days=6),
            "adults": 1,
            "room_type_id": self.room_type1.id,
            "partner_id": self.host1.id,
            "pms_property_id": self.pms_property1.id,
            "folio_id": self.reservation_1.folio_id.id,
        }
        self.reservation_2 = self.env["pms.reservation"].create(reservation2_vals)
        self.reservation_3 = self.env["pms.reservation"].create(reservation3_vals)
        folio_1 = self.reservation_1.folio_id
        PmsReservation = self.env["pms.reservation"]

        # ACTION
        freezer = freeze_time("2012-01-16 10:00:00")
        freezer.start()
        PmsReservation.auto_arrival_delayed()

        arrival_delayed_reservations = folio_1.reservation_ids.filtered(
            lambda r: r.state == "arrival_delayed"
        )

        # ASSERT
        self.assertEqual(
            len(arrival_delayed_reservations),
            3,
            "Reservations not set like No Show",
        )
        freezer.stop()

    @freeze_time("2012-01-14")
    def test_auto_arrival_delayed_checkout(self):
        """
        The state of reservation 'arrival_delayed' happen when the checkin day
        has already passed and the resrvation had not yet changed its state to onboard.
        But, if checkout day is passed without checkout, the reservation pass to
        departure delayed with a reservation note warning

        The date that was previously set was 2012-01-14,
        it was advanced two days (to 2012-01-16).
        There are three reservations with checkout day on 2012-01-15,
        after invoking the method auto_arrival_delayed
        those reservation change their state to 'departure_delayed'
        """

        # ARRANGE
        self.host2 = self.env["res.partner"].create(
            {
                "name": "Carlos",
                "mobile": "654667733",
                "email": "carlos@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "61369791H",
                "valid_from": datetime.date.today(),
                "partner_id": self.host2.id,
            }
        )
        self.host3 = self.env["res.partner"].create(
            {
                "name": "Enmanuel",
                "mobile": "654667733",
                "email": "enmanuel@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "53563260D",
                "valid_from": datetime.date.today(),
                "partner_id": self.host3.id,
            }
        )
        self.host4 = self.env["res.partner"].create(
            {
                "name": "Enrique",
                "mobile": "654667733",
                "email": "enrique@example.com",
                "birthdate_date": "1995-12-10",
                "gender": "male",
            }
        )
        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "63742138F",
                "valid_from": datetime.date.today(),
                "partner_id": self.host4.id,
            }
        )
        self.reservation_1.write(
            {
                "checkin": datetime.date.today(),
                "checkout": datetime.date.today() + datetime.timedelta(days=1),
                "adults": 1,
            }
        )
        reservation2_vals = {
            "checkin": datetime.date.today(),
            "checkout": datetime.date.today() + datetime.timedelta(days=1),
            "adults": 1,
            "room_type_id": self.room_type1.id,
            "partner_id": self.host1.id,
            "pms_property_id": self.pms_property1.id,
            "folio_id": self.reservation_1.folio_id.id,
        }
        reservation3_vals = {
            "checkin": datetime.date.today(),
            "checkout": datetime.date.today() + datetime.timedelta(days=1),
            "adults": 1,
            "room_type_id": self.room_type1.id,
            "partner_id": self.host1.id,
            "pms_property_id": self.pms_property1.id,
            "folio_id": self.reservation_1.folio_id.id,
        }
        self.reservation_2 = self.env["pms.reservation"].create(reservation2_vals)
        self.reservation_3 = self.env["pms.reservation"].create(reservation3_vals)
        folio_1 = self.reservation_1.folio_id
        PmsReservation = self.env["pms.reservation"]

        # ACTION
        freezer = freeze_time("2012-01-16 10:00:00")
        freezer.start()
        PmsReservation.auto_arrival_delayed()

        departure_delayed_reservations = folio_1.reservation_ids.filtered(
            lambda r: r.state == "departure_delayed"
        )

        # ASSERT
        self.assertEqual(
            len(departure_delayed_reservations),
            3,
            "Reservations not set like No Show",
        )
        freezer.stop()

    @freeze_time("2012-01-14")
    def test_auto_departure_delayed(self):
        """
        When it's checkout dat and the reservation
        was in 'onboard' state, that state change to
        'departure_delayed' if the manual checkout wasn't performed.

        The date that was previously set was 2012-01-14,
        it was advanced two days (to 2012-01-17).
        Reservation1 has checkout day on 2012-01-17,
         after invoking the method auto_departure_delayed
        this reservation change their state to 'auto_departure_delayed'
        """

        # ARRANGE
        self.reservation_1.write(
            {
                "checkin": datetime.date.today(),
                "checkout": datetime.date.today() + datetime.timedelta(days=3),
                "adults": 1,
            }
        )
        PmsReservation = self.env["pms.reservation"]
        self.checkin1.action_on_board()

        # ACTION
        freezer = freeze_time("2012-01-17 12:00:00")
        freezer.start()
        PmsReservation.auto_departure_delayed()

        freezer.stop()
        # ASSERT
        self.assertEqual(
            self.reservation_1.state,
            "departure_delayed",
            "Reservations not set like Departure delayed",
        )

    # REVIEW: Redesing constrains mobile&mail control
    # @freeze_time("2010-12-10")
    # def test_not_valid_emails(self):
    #     # TEST CASES
    #     # Check that the email format is incorrect

    #     # ARRANGE
    #     reservation = self.env["pms.reservation"].create(
    #         {
    #             "checkin": datetime.date.today(),
    #             "checkout": datetime.date.today() + datetime.timedelta(days=3),
    #             "room_type_id": self.room_type1.id,
    #             "partner_id": self.env.ref("base.res_partner_12").id,
    #             "adults": 3,
    #             "pms_property_id": self.pms_property1.id,
    #         }
    #     )
    #     test_cases = [
    #         "myemail",
    #         "myemail@",
    #         "myemail@",
    #         "myemail@.com",
    #         ".myemail",
    #         ".myemail@",
    #         ".myemail@.com" ".myemail@.com." "123myemail@aaa.com",
    #     ]
    #     for mail in test_cases:
    #         with self.subTest(i=mail):
    #             with self.assertRaises(
    #                 ValidationError, msg="Email format is correct and shouldn't"
    #             ):
    #                 reservation.write(
    #                     {
    #                         "checkin_partner_ids": [
    #                             (
    #                                 0,
    #                                 False,
    #                                 {
    #                                     "name": "Carlos",
    #                                     "email": mail,
    #                                 },
    #                             )
    #                         ]
    #                     }
    #                 )

    # @freeze_time("2014-12-10")
    # def test_valid_emails(self):
    #     # TEST CASES
    #     # Check that the email format is correct

    #     # ARRANGE
    #     reservation = self.env["pms.reservation"].create(
    #         {
    #             "checkin": datetime.date.today(),
    #             "checkout": datetime.date.today() + datetime.timedelta(days=4),
    #             "room_type_id": self.room_type1.id,
    #             "partner_id": self.env.ref("base.res_partner_12").id,
    #             "adults": 3,
    #             "pms_property_id": self.pms_property1.id,
    #         }
    #     )
    #     test_cases = [
    #         "hello@commitsun.com",
    #         "hi.welcome@commitsun.com",
    #         "hi.welcome@dev.commitsun.com",
    #         "hi.welcome@dev-commitsun.com",
    #         "john.doe@xxx.yyy.zzz",
    #     ]
    #     for mail in test_cases:
    #         with self.subTest(i=mail):
    #             guest = self.env["pms.checkin.partner"].create(
    #                 {
    #                     "name": "Carlos",
    #                     "email": mail,
    #                     "reservation_id": reservation.id,
    #                 }
    #             )
    #             self.assertEqual(
    #                 mail,
    #                 guest.email,
    #             )
    #             guest.unlink()

    # @freeze_time("2016-12-10")
    # def test_not_valid_phone(self):
    #     # TEST CASES
    #     # Check that the phone format is incorrect

    #     # ARRANGE
    #     reservation = self.env["pms.reservation"].create(
    #         {
    #             "checkin": datetime.date.today(),
    #             "checkout": datetime.date.today() + datetime.timedelta(days=1),
    #             "room_type_id": self.room_type1.id,
    #             "partner_id": self.env.ref("base.res_partner_12").id,
    #             "adults": 3,
    #             "pms_property_id": self.pms_property1.id,
    #         }
    #     )
    #     test_cases = [
    #         "phone",
    #         "123456789123",
    #         "123.456.789",
    #         "123",
    #         "123123",
    #     ]
    #     for phone in test_cases:
    #         with self.subTest(i=phone):
    #             with self.assertRaises(
    #                 ValidationError, msg="Phone format is correct and shouldn't"
    #             ):
    #                 self.env["pms.checkin.partner"].create(
    #                     {
    #                         "name": "Carlos",
    #                         "mobile": phone,
    #                         "reservation_id": reservation.id,
    #                     }
    #                 )

    # @freeze_time("2018-12-10")
    # def test_valid_phones(self):
    #     # TEST CASES
    #     # Check that the phone format is correct

    #     # ARRANGE
    #     reservation = self.env["pms.reservation"].create(
    #         {
    #             "checkin": datetime.date.today(),
    #             "checkout": datetime.date.today() + datetime.timedelta(days=5),
    #             "room_type_id": self.room_type1.id,
    #             "partner_id": self.env.ref("base.res_partner_12").id,
    #             "adults": 3,
    #             "pms_property_id": self.pms_property1.id,
    #         }
    #     )
    #     test_cases = [
    #         "981 981 981",
    #         "981981981",
    #         "981 98 98 98",
    #     ]
    #     for mobile in test_cases:
    #         with self.subTest(i=mobile):
    #             guest = self.env["pms.checkin.partner"].create(
    #                 {
    #                     "name": "Carlos",
    #                     "mobile": mobile,
    #                     "reservation_id": reservation.id,
    #                 }
    #             )
    #             self.assertEqual(
    #                 mobile,
    #                 guest.mobile,
    #             )

    def test_complete_checkin_data_with_partner_data(self):
        """
        When a partner is asociated with a checkin, checkin data
        will be equal to the partner data

        Host1:
            "email": "miguel@example.com",
            "birthdate_date": "1995-12-10",
            "gender": "male",

        Checkin1:
            "partner_id": host1.id

        So after this:
        Checkin1:
            "email": "miguel@example.com",
            "birthdate_date": "1995-12-10",
            "gender": "male",
        """
        # ARRANGE
        partner_data = [self.host1.birthdate_date, self.host1.email, self.host1.gender]
        checkin_data = [
            self.checkin1.birthdate_date,
            self.checkin1.email,
            self.checkin1.gender,
        ]

        # ASSERT
        for i in [0, 1, 2]:
            self.assertEqual(
                partner_data[i],
                checkin_data[i],
                "Checkin data must be the same as partner data ",
            )

    def test_create_partner_when_checkin_has_enought_data(self):
        """
        Check that partner is created when the necessary minimum data is entered
        into checkin_partner data
        """
        # ACT & ASSERT
        checkin = self.env["pms.checkin.partner"].create(
            {
                "firstname": "Pepe",
                "lastname": "Paz",
                "document_type": self.id_category.id,
                "document_number": "77156490T",
                "reservation_id": self.reservation_1.id,
            }
        )

        # ASSERT
        self.assertTrue(
            checkin.partner_id,
            "Partner should have been created and associated with the checkin",
        )

    def test_not_create_partner_checkin_hasnt_enought_data(self):
        """
        Check that partner is not created when the necessary minimum data isn't entered
        into checkin_partner data, in this case document_id and document_number
        """
        # ACT & ASSERT
        checkin = self.env["pms.checkin.partner"].create(
            {
                "firstname": "Pepe",
                "lastname": "Paz",
                "email": "pepepaz@gmail.com",
                "mobile": "666777777",
                "reservation_id": self.reservation_1.id,
            }
        )

        # ASSERT
        self.assertFalse(
            checkin.partner_id,
            "Partner mustn't have been created and associated with the checkin",
        )

    def test_add_partner_data_from_checkin(self):
        """
        If the checkin_partner has some data that the partner doesn't have,
        these are saved in the partner

        In this case, host1 hasn't mobile but the checkin_partner associated with it does,
        so the mobile of checkin_partner is added to the partner data

        Note that if the mobile is entered before partnee was associated, this or other fields
        are overwritten by the partner's fields. In this case it is entered once the partner has
        already been associated
        """
        # ARRANGE
        self.checkin1.mobile = "666777888"
        # ASSERT
        self.assertTrue(self.host1.mobile, "Partner mobile must be added")

    def test_partner_id_numbers_created_from_checkin(self):
        """
        Some of the required data of the checkin_partner to create the partner are document_type
        and document_number, with them an id_number is created associated with the partner that
        has just been created.
        In this test it is verified that this document has been created correctly
        """
        # ACT & ARRANGE
        checkin = self.env["pms.checkin.partner"].create(
            {
                "firstname": "Pepe",
                "lastname": "Paz",
                "document_type": self.id_category.id,
                "document_number": "77156490T",
                "reservation_id": self.reservation_1.id,
            }
        )

        checkin.flush()

        # ASSERT
        self.assertTrue(
            checkin.partner_id.id_numbers,
            "Partner id_number should have been created and hasn't been",
        )

    def test_partner_not_modified_when_checkin_modified(self):
        """
        If a partner is associated with a checkin
        and some of their data is modified in the checkin,
        they will not be modified in the partner
        """
        # ARRANGE
        self.checkin1.email = "prueba@gmail.com"

        # ASSERT
        self.assertNotEqual(
            self.host1.email,
            self.checkin1.email,
            "Checkin partner email and partner email shouldn't match",
        )

    def test_partner_modified_previous_checkin_not_modified(self):
        """
        If a partner modifies any of its fields, these change mustn't be reflected
        in the previous checkins associated with it
        """
        # ARRANGE
        self.checkin1.flush()
        self.host1.gender = "female"
        # ASSERT
        self.assertNotEqual(
            self.host1.gender,
            self.checkin1.gender,
            "Checkin partner gender and partner gender shouldn't match",
        )

    def test_add_partner_if_exists_from_checkin(self):
        """
        Check when a document_type and document_number are entered in a checkin if this
        document already existes and is associated with a partner, this partner will be
        associated with the checkin
        """
        # ACT
        host = self.env["res.partner"].create(
            {
                "name": "Ricardo",
                "mobile": "666555666",
                "email": "ricardo@example.com",
                "birthdate_date": "1995-11-14",
                "gender": "male",
            }
        )

        self.env["res.partner.id_number"].create(
            {
                "category_id": self.id_category.id,
                "name": "55562998N",
                "partner_id": host.id,
            }
        )

        # ARRANGE
        checkin = self.env["pms.checkin.partner"].create(
            {
                "document_type": self.id_category.id,
                "document_number": "55562998N",
                "reservation_id": self.reservation_1.id,
            }
        )

        # ASSERT
        self.assertEqual(
            checkin.partner_id.id,
            host.id,
            "Checkin partner_id must be the same as the one who has that document",
        )

    def test_is_possible_customer_by_email(self):
        """
        It is checked that the field possible_existing_customer_ids
        exists in a checkin partner with an email from a res.partner saved
        in the DB.
        ----------------
        A res.partner is created with the name and email fields. A checkin partner
        is created by adding the same email as the res.partner. Then it is
        checked that some possible_existing_customer_ids exists.
        """
        # ARRANGE
        partner = self.env["res.partner"].create(
            {
                "name": "Courtney Campbell",
                "email": "courtney@example.com",
            }
        )
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=3)
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": checkin,
                "checkout": checkout,
                "room_type_id": self.room_type1.id,
                "pms_property_id": self.pms_property1.id,
                "partner_name": partner.name,
                "email": partner.email,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # ACT
        checkin = self.env["pms.checkin.partner"].create(
            {
                "name": partner.name,
                "email": partner.email,
                "reservation_id": reservation.id,
            }
        )
        # ASSERT
        self.assertTrue(
            checkin.possible_existing_customer_ids,
            "No customer found with this email",
        )

    def test_is_possible_customer_by_mobile(self):
        """
        It is checked that the field possible_existing_customer_ids
        exists in a checkin partner with a mobile from a res.partner saved
        in the DB.
        ----------------
        A res.partner is created with the name and email fields. A checkin partner
        is created by adding the same mobile as the res.partner. Then it is
        checked that some possible_existing_customer_ids exists.
        """
        # ARRANGE
        partner = self.env["res.partner"].create(
            {
                "name": "Ledicia Sandoval",
                "mobile": "615369231",
            }
        )
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=3)
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": checkin,
                "checkout": checkout,
                "room_type_id": self.room_type1.id,
                "pms_property_id": self.pms_property1.id,
                "partner_name": partner.name,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        # ACT
        checkin = self.env["pms.checkin.partner"].create(
            {
                "name": partner.name,
                "mobile": partner.mobile,
                "reservation_id": reservation.id,
            }
        )
        # ASSERT
        self.assertTrue(
            checkin.possible_existing_customer_ids,
            "No customer found with this mobile",
        )

    def test_add_possible_customer(self):
        """
        Check that a partner was correctly added to the checkin partner
        after launching the add_partner() method of the several partners wizard
        ---------------
        A res.partner is created with name, email and mobile. A checkin partner is
        created with the email field equal to that of the res.partner created before.
        The wizard is created with the checkin partner id and the partner added to the
        possible_existing_customer_ids field. The add_partner method of the wizard
        is launched and it is checked that the partner was correctly added to the
        checkin partner.
        """
        # ARRANGE
        partner = self.env["res.partner"].create(
            {
                "name": "Serafín Rivas",
                "email": "serafin@example.com",
                "mobile": "60595595",
            }
        )
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=3)
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": checkin,
                "checkout": checkout,
                "room_type_id": self.room_type1.id,
                "pms_property_id": self.pms_property1.id,
                "partner_name": partner.name,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        checkin = self.env["pms.checkin.partner"].create(
            {
                "name": partner.name,
                "email": partner.email,
                "reservation_id": reservation.id,
            }
        )

        several_partners_wizard = self.env["pms.several.partners.wizard"].create(
            {
                "checkin_partner_id": checkin.id,
                "possible_existing_customer_ids": [(6, 0, [partner.id])],
            }
        )
        # ACT
        several_partners_wizard.add_partner()
        # ASSERT
        self.assertEqual(
            checkin.partner_id.id,
            partner.id,
            "The partner was not added to the checkin partner ",
        )

    def test_not_add_several_possibles_customers(self):
        """
        Check that multiple partners cannot be added to a checkin partner
        from the several partners wizard.
        ---------------
        Two res.partner are created with name, email and mobile. A checkin partner is
        created with the email field equal to that of the partner1 created before.
        The wizard is created with the checkin partner id and the two partners added to the
        possible_existing_customer_ids field. The add_partner method of the wizard
        is launched and it is verified that a Validation_Error was raised.
        """
        # ARRANGE
        partner1 = self.env["res.partner"].create(
            {
                "name": "Serafín Rivas",
                "email": "serafin@example.com",
                "mobile": "60595595",
            }
        )
        partner2 = self.env["res.partner"].create(
            {
                "name": "Simon",
                "mobile": "654667733",
                "email": "simon@example.com",
            }
        )

        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=3)
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": checkin,
                "checkout": checkout,
                "room_type_id": self.room_type1.id,
                "pms_property_id": self.pms_property1.id,
                "partner_name": partner1.name,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )

        checkin = self.env["pms.checkin.partner"].create(
            {
                "name": partner1.name,
                "email": partner1.email,
                "reservation_id": reservation.id,
            }
        )

        several_partners_wizard = self.env["pms.several.partners.wizard"].create(
            {
                "checkin_partner_id": checkin.id,
                "possible_existing_customer_ids": [(6, 0, [partner1.id, partner2.id])],
            }
        )

        # ACT AND ASSERT
        with self.assertRaises(
            ValidationError,
            msg="Two partners cannot be added to the checkin partner",
        ):
            several_partners_wizard.add_partner()

    def test_not_add_any_possibles_customers(self):
        """
        Check that the possible_existing_customer_ids field of the several
        partners wizard can be left empty and then launch the add_partner()
        method of this wizard to add a partner in checkin_partner.
        ---------------
        A checkin_partner is created. The wizard is created without the
        possible_existing_customer_ids field. The add_partner method of
        the wizard is launched and it is verified that a Validation_Error
        was raised.
        """

        # ARRANGE
        checkin = fields.date.today()
        checkout = fields.date.today() + datetime.timedelta(days=3)
        reservation = self.env["pms.reservation"].create(
            {
                "checkin": checkin,
                "checkout": checkout,
                "room_type_id": self.room_type1.id,
                "pms_property_id": self.pms_property1.id,
                "partner_name": "Rosa Costa",
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        checkin = self.env["pms.checkin.partner"].create(
            {"name": "Rosa Costa", "reservation_id": reservation.id}
        )

        several_partners_wizard = self.env["pms.several.partners.wizard"].create(
            {
                "checkin_partner_id": checkin.id,
            }
        )

        # ACT AND ASSERT
        with self.assertRaises(
            ValidationError,
            msg="A partner can be added to the checkin partner",
        ):
            several_partners_wizard.add_partner()

    def test_calculate_dni_expedition_date_from_validity_date_age_lt_30(self):
        """
        Check that the calculate_doc_type_expedition_date_from_validity_date()
        method calculates correctly the expedition_date of an id category DNI
        when the age is less than 30.
        -------------
        We launch the method calculate_doc_type_expedition_date_from_validity_date
        with the parameters doc_type_id DNI, birthdate calculated so that the age
        is = 20 years old and document_date = today + 1 year. The expected
        expedition date has to be doc_date - 5 years
        """
        doc_date = fields.date.today() + relativedelta(years=1)
        doc_date_str = str(doc_date)

        # age=20 years old
        birthdate = fields.date.today() - relativedelta(years=20)
        birthdate_str = str(birthdate)

        # expected_expedition_date = doc_date - 5 years
        expected_exp_date = doc_date - relativedelta(years=5)
        expedition_date = (
            self.checkin1.calculate_doc_type_expedition_date_from_validity_date(
                self.id_category, doc_date_str, birthdate_str
            )
        )
        date_expedition_date = datetime.date(
            year=expedition_date.year,
            month=expedition_date.month,
            day=expedition_date.day,
        )
        self.assertEqual(
            date_expedition_date,
            expected_exp_date,
            "Expedition date doesn't correspond with expected expedition date",
        )

    def test_calculate_dni_expedition_date_from_validity_date_age_gt_30(self):
        """
        Check that the calculate_doc_type_expedition_date_from_validity_date()
        method calculates correctly the expedition_date of an id category DNI
        when the age is greater than 30.
        -------------
        We launch the method calculate_doc_type_expedition_date_from_validity_date
        with the parameters doc_type_id DNI, birthdate calculated so that the age
        is = 40 years old and document_date = today + 1 year. The expected
        expedition date has to be doc_date - 10 years
        """
        doc_date = fields.date.today() + relativedelta(years=1)
        doc_date_str = str(doc_date)

        # age=40 years old
        birthdate = fields.date.today() - relativedelta(years=40)
        birthdate_str = str(birthdate)

        # expected_expedition_date = doc_date - 10 years
        expected_exp_date = doc_date - relativedelta(years=10)
        expedition_date = (
            self.checkin1.calculate_doc_type_expedition_date_from_validity_date(
                self.id_category, doc_date_str, birthdate_str
            )
        )
        date_expedition_date = datetime.date(
            year=expedition_date.year,
            month=expedition_date.month,
            day=expedition_date.day,
        )
        self.assertEqual(
            date_expedition_date,
            expected_exp_date,
            "Expedition date doesn't correspond with expected expedition date",
        )

    def test_calculate_passport_expedition_date_from_validity_date_age_lt_30(self):
        """
        Check that the calculate_doc_type_expedition_date_from_validity_date()
        method calculates correctly the expedition_date of an id category Passport
        when the age is less than 30.
        -------------
        We launch the method calculate_doc_type_expedition_date_from_validity_date
        with the parameters doc_type_id Passport, birthdate calculated so that the age
        is = 20 years old and document_date = today + 1 year. The expected
        expedition date has to be doc_date - 5 years
        """
        doc_date = fields.date.today() + relativedelta(years=1)
        doc_date_str = str(doc_date)

        # age=20 years old
        birthdate = fields.date.today() - relativedelta(years=20)
        birthdate_str = str(birthdate)

        # expected_expedition_date = doc_date - 5 years
        expected_exp_date = doc_date - relativedelta(years=5)
        expedition_date = (
            self.checkin1.calculate_doc_type_expedition_date_from_validity_date(
                self.id_category, doc_date_str, birthdate_str
            )
        )
        date_expedition_date = datetime.date(
            year=expedition_date.year,
            month=expedition_date.month,
            day=expedition_date.day,
        )
        self.assertEqual(
            date_expedition_date,
            expected_exp_date,
            "Expedition date doesn't correspond with expected expedition date",
        )

    def test_calculate_passport_expedition_date_from_validity_date_age_gt_30(self):
        """
        Check that the calculate_doc_type_expedition_date_from_validity_date()
        method calculates correctly the expedition_date of an id category Passport
        when the age is greater than 30.
        -------------
        We launch the method calculate_doc_type_expedition_date_from_validity_date
        with the parameters doc_type_id Passport, birthdate calculated so that the age
        is = 40 years old and document_date = today + 1 year. The expected
        expedition date has to be doc_date - 10 years
        """
        doc_type_id = self.env["res.partner.id_category"].search([("code", "=", "P")])
        doc_date = fields.date.today() + relativedelta(years=1)
        doc_date_str = str(doc_date)

        # age=40 years old
        birthdate = fields.date.today() - relativedelta(years=40)
        birthdate_str = str(birthdate)

        # expected_expedition_date = doc_date - 10 years
        expected_exp_date = doc_date - relativedelta(years=10)
        expedition_date = (
            self.checkin1.calculate_doc_type_expedition_date_from_validity_date(
                doc_type_id, doc_date_str, birthdate_str
            )
        )
        date_expedition_date = datetime.date(
            year=expedition_date.year,
            month=expedition_date.month,
            day=expedition_date.day,
        )
        self.assertEqual(
            date_expedition_date,
            expected_exp_date,
            "Expedition date doesn't correspond with expected expedition date",
        )

    def test_calculate_drive_license_expedition_date_from_validity_date_age_lt_70(self):
        """
        Check that the calculate_doc_type_expedition_date_from_validity_date()
        method calculates correctly the expedition_date of an id category Driving
        License when the age is lesser than 70.
        -------------
        We launch the method calculate_doc_type_expedition_date_from_validity_date
        with the parameters doc_type_id DNI, birthdate calculated so that the age
        is = 40 years old and document_date = today + 1 year. The expected
        expedition date has to be doc_date - 10 years
        """
        doc_type_id = self.env["res.partner.id_category"].search([("code", "=", "C")])
        doc_date = fields.date.today() + relativedelta(years=1)
        doc_date_str = str(doc_date)

        # age=40 years old
        birthdate = fields.date.today() - relativedelta(years=40)
        birthdate_str = str(birthdate)

        # expected_expedition_date = doc_date - 10 years
        expected_exp_date = doc_date - relativedelta(years=10)
        expedition_date = (
            self.checkin1.calculate_doc_type_expedition_date_from_validity_date(
                doc_type_id, doc_date_str, birthdate_str
            )
        )
        date_expedition_date = datetime.date(
            year=expedition_date.year,
            month=expedition_date.month,
            day=expedition_date.day,
        )
        self.assertEqual(
            date_expedition_date,
            expected_exp_date,
            "Expedition date doesn't correspond with expected expedition date",
        )

    def test_calculate_expedition_date(self):
        """
        Check that if the value of the doc_date is less than today,
        the method calculate_doc_type_expedition_date_from_validity_date
        returns the value of the doc_date as expedition_date.
        -----------
        We launch the method calculate_doc_type_expedition_date_from_validity_date
        with the parameters doc_type_id DNI, birthdate calculated so that the age
        is = 20 years old and document_date = today - 1 year. The expected
        expedition date has to be the value of doc_date.
        """
        doc_type_id = self.env["res.partner.id_category"].search([("code", "=", "D")])
        doc_date = fields.date.today() - relativedelta(years=1)
        doc_date_str = str(doc_date)
        birthdate = fields.date.today() - relativedelta(years=20)
        birthdate_str = str(birthdate)
        expedition_date = (
            self.checkin1.calculate_doc_type_expedition_date_from_validity_date(
                doc_type_id, doc_date_str, birthdate_str
            )
        )
        date_expedition_date = datetime.date(
            year=expedition_date.year,
            month=expedition_date.month,
            day=expedition_date.day,
        )
        self.assertEqual(
            date_expedition_date,
            doc_date,
            "Expedition date doesn't correspond with expected expedition date",
        )

    def test_save_checkin_from_portal(self):
        """
        Check by subtesting that a checkin partner is saved correctly
        with the _save_data_from_portal() method.
        ---------
        A reservation is created with an adult, and it will create a checkin partner.
        A dictionary is created with the values to be saved and with the key 'id'
        equal to the id of the checkin_partner created when the reservation was
        created. We launch the _save_data_from_portal() method, passing the created
        dictionary as a parameter. Then it is verified that the value of each key
        in the dictionary corresponds to the fields of the saved checkin_partner.
        """
        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": datetime.date.today() + datetime.timedelta(days=10),
                "checkout": datetime.date.today() + datetime.timedelta(days=13),
                "room_type_id": self.room_type1.id,
                "partner_id": self.host1.id,
                "adults": 1,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        checkin_partner_id = self.reservation.checkin_partner_ids[0]
        checkin_partner_vals = {
            "checkin_partner_id": checkin_partner_id.id,
            "id": checkin_partner_id.id,
            "firstname": "Serafín",
            "lastname": "Rivas",
            "lastname2": "Gonzalez",
            "document_type": self.id_category.name,
            "document_number": "18038946T",
            "document_expedition_date": "2010-10-07",
            "birthdate_date": "1983-10-05",
            "mobile": "60595595",
            "email": "serafin@example.com",
            "gender": "male",
            "nationality_id": "1",
            "residence_state_id": "1",
        }
        checkin_partner_id._save_data_from_portal(checkin_partner_vals)
        checkin_partner_vals.update(
            {
                "birthdate_date": datetime.date(1983, 10, 5),
                "document_expedition_date": datetime.date(2010, 10, 7),
                "nationality_id": self.env["res.country"].search([("id", "=", 1)]),
                "residence_state_id": self.env["res.country.state"].browse(1),
                "document_type": self.id_category,
            }
        )
        for key in checkin_partner_vals:
            with self.subTest(k=key):
                self.assertEqual(
                    self.reservation.checkin_partner_ids[0][key],
                    checkin_partner_vals[key],
                    "The value of " + key + " is not correctly established",
                )

    def test_compute_partner_fields(self):
        """
        Check that the computes of the checkin_partner fields related to your partner correctly
        add these fields to the checkin_partner.
        ---------------------------------------
        A reservation is created with an adult (checkin_partner) ql which is saved in the
        checkin_partner_id variable, a partner is also created with all the fields that are
        related to the checkin_partner fields. The partner is added to the partner_id field
        of the checkin_partner and, through subtests, it is verified that the fields of the
        partner and the associated checkin_partner match.
        """
        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": datetime.date.today() + datetime.timedelta(days=1),
                "checkout": datetime.date.today() + datetime.timedelta(days=2),
                "room_type_id": self.room_type1.id,
                "partner_id": self.host1.id,
                "adults": 1,
                "pms_property_id": self.pms_property1.id,
                "sale_channel_origin_id": self.sale_channel_direct1.id,
            }
        )
        checkin_partner_id = self.reservation.checkin_partner_ids[0]
        nationality_id = self.env["res.country"].browse(1)
        state_id = self.env["res.country.state"].browse(1)
        partner_vals = {
            "firstname": "Paz",
            "lastname": "Valenzuela",
            "lastname2": "Soto",
            "email": "paz@example.com",
            "birthdate_date": datetime.date(1980, 10, 5),
            "gender": "female",
            "mobile": "666555444",
            "phone": "123456789",
            "nationality_id": nationality_id.id,
            "residence_street": "Calle 123",
            "residence_street2": "Avda. Constitución 123",
            "residence_zip": "15700",
            "residence_city": "City Residence",
            "residence_country_id": nationality_id.id,
            "residence_state_id": state_id.id,
            # "pms_checkin_partner_ids": checkin_partner_id,
        }
        self.partner_id = self.env["res.partner"].create(partner_vals)

        partner_vals.update(
            {
                "nationality_id": nationality_id,
                "residence_country_id": nationality_id,
                "residence_state_id": state_id,
            }
        )

        checkin_partner_id.partner_id = self.partner_id.id
        for key in partner_vals:
            if key != "pms_checkin_partner_ids":
                with self.subTest(k=key):
                    self.assertEqual(
                        self.reservation.checkin_partner_ids[0][key],
                        self.partner_id[key],
                        "The value of " + key + " is not correctly established",
                    )
