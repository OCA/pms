import datetime

from freezegun import freeze_time

from odoo import fields

from .common import TestPms


class TestPmsService(TestPms):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # create room type
        cls.room_type_double = cls.env["pms.room.type"].create(
            {
                "pms_property_ids": [cls.pms_property1.id],
                "name": "Double Test",
                "default_code": "DBL_Test",
                "class_id": cls.room_type_class1.id,
            }
        )
        # create rooms
        cls.room1 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Double 101",
                "room_type_id": cls.room_type_double.id,
                "capacity": 2,
                "extra_beds_allowed": 1,
            }
        )

        cls.room2 = cls.env["pms.room"].create(
            {
                "pms_property_id": cls.pms_property1.id,
                "name": "Double 102",
                "room_type_id": cls.room_type_double.id,
                "capacity": 2,
                "extra_beds_allowed": 1,
            }
        )
        cls.partner1 = cls.env["res.partner"].create(
            {
                "firstname": "María",
                "lastname": "",
                "email": "jaime@example.com",
                "birthdate_date": "1983-03-01",
                "gender": "male",
            }
        )
        cls.sale_channel_door = cls.env["pms.sale.channel"].create(
            {"name": "Door", "channel_type": "direct"}
        )
        cls.sale_channel_phone = cls.env["pms.sale.channel"].create(
            {"name": "Phone", "channel_type": "direct"}
        )
        cls.sale_channel_mail = cls.env["pms.sale.channel"].create(
            {"name": "Mail", "channel_type": "direct"}
        )

    @freeze_time("2002-01-01")
    def test_reservation_sale_origin_in_board_service(self):
        """
        When a reservation is created with board_service, the sale_channel_origin_id
        is indicated in reservation. Therefore, the board_service takes
        the sale_channel_origin of its reservation

        Reservation --> sale_channel_origin_id = Door
                    |
                    --> service.sale_channel_origin_id? It must be Door
        """
        # ARRANGE
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
            }
        )

        self.board_service1 = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service 1",
                "default_code": "CB1",
            }
        )
        self.board_service_line1 = self.env["pms.board.service.line"].create(
            {
                "product_id": self.product1.id,
                "pms_board_service_id": self.board_service1.id,
                "amount": 10,
            }
        )

        self.board_service_room_type1 = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": self.board_service1.id,
            }
        )
        # ACT
        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=2),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "board_service_room_id": self.board_service_room_type1.id,
                "sale_channel_origin_id": self.sale_channel_door.id,
            }
        )
        # ASSERT
        self.assertEqual(
            self.reservation.sale_channel_origin_id,
            self.reservation.service_ids.sale_channel_origin_id,
            "sale_channel_origin of board_Service must be the same as its reservation",
        )

    @freeze_time("2002-01-11")
    def test_change_origin_board_service_not_change_reservation_origin(self):
        """
        When you change the sale_channel_origin_id of a board_service in a reservation
        that matched the origin of its reservation, if that reservation has reservation_lines
        with that sale_channel_id, it doesn't change the origin of reservation

        Reservation --> sale_channel_origin = Door          sale_channel_ids = Door
                    |
                    --> board_services.sale_channel_origin = Door

        Change board_service origin to Mail
        Reservation --> sale_channel_origin = Door          sale_channel_ids = {Door, Mail}
                    |
                    --> board_services.sale_channel_origin = Mail

        """
        # ARRANGE
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
            }
        )

        self.board_service1 = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service 1",
                "default_code": "CB1",
            }
        )
        self.board_service_line1 = self.env["pms.board.service.line"].create(
            {
                "product_id": self.product1.id,
                "pms_board_service_id": self.board_service1.id,
                "amount": 10,
            }
        )

        self.board_service_room_type1 = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": self.board_service1.id,
            }
        )

        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=3),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "board_service_room_id": self.board_service_room_type1.id,
                "sale_channel_origin_id": self.sale_channel_door.id,
            }
        )
        # ACT
        self.reservation.service_ids.sale_channel_origin_id = self.sale_channel_mail.id
        # ASSERT
        self.assertNotEqual(
            self.reservation.sale_channel_origin_id,
            self.reservation.service_ids.sale_channel_origin_id,
            """sale_channel_origin_id mustn't match
            with sale_channel_origin_id of its reservation""",
        )

    @freeze_time("2002-01-17")
    def test_change_origin_board_service_in_sale_channels(self):
        """
        When sale_channel_origin_id of board_service is changed, the sale_channel_ids
        of its reservation and folio are recalculated. Check that these calculations are correct

        Reservation --> sale_channel_origin = Door        sale_channel_ids = Door
                    |
                    ---> board_service.sale_channel_origin = Door

        Change origin of board services to Phone and
        check sale_channel_ids of reservation and folio:
        Reservation --> sale_channel_origin = Door        sale_channel_ids = {Door, Phone}
                    |
                    ---> board_service.sale_channel_origin = Phone

        Reservation.folio_id.sale_channel_ids = {Door, Phone}
        """
        # ARRANGE
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
            }
        )

        self.board_service1 = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service 1",
                "default_code": "CB1",
            }
        )
        self.board_service_line1 = self.env["pms.board.service.line"].create(
            {
                "product_id": self.product1.id,
                "pms_board_service_id": self.board_service1.id,
                "amount": 10,
            }
        )

        self.board_service_room_type1 = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": self.board_service1.id,
            }
        )
        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=3),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "board_service_room_id": self.board_service_room_type1.id,
                "sale_channel_origin_id": self.sale_channel_door.id,
            }
        )
        # ACT
        self.reservation.service_ids.sale_channel_origin_id = self.sale_channel_phone

        sale_channel_ids = [
            self.reservation.folio_id.sale_channel_ids.ids,
            self.reservation.sale_channel_ids.ids,
        ]

        expected_sale_channel_ids = [
            self.sale_channel_door.id,
            self.sale_channel_phone.id,
        ]
        # ASSERT
        for sale_channel in sale_channel_ids:
            with self.subTest(k=sale_channel):
                self.assertItemsEqual(
                    sale_channel,
                    expected_sale_channel_ids,
                    "sale_channel_ids must contain sale_channel_origin_id of all board_service",
                )

    @freeze_time("2002-01-19")
    def test_change_origin_reservation_change_origin_services(self):
        """
        When sale_channel_origin_id of reservation is changed,
        sale_channel_origin_id of its services having the same origin
        must also be changed

        Reservation ---> sale_channel_origin = Door
                    |
                    --> service.sale_channel_origin = Door

        Change sale_channel_origin to Mail, expected results:
        Reservation ---> sale_channel_origin = Mail
                    |
                    --> service.sale_channel_origin = Mail ----CHECKING THIS---

        """
        # ARRANGE
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
            }
        )

        self.board_service1 = self.env["pms.board.service"].create(
            {
                "name": "Test Board Service 1",
                "default_code": "CB1",
            }
        )
        self.board_service_line1 = self.env["pms.board.service.line"].create(
            {
                "product_id": self.product1.id,
                "pms_board_service_id": self.board_service1.id,
                "amount": 10,
            }
        )

        self.board_service_room_type1 = self.env["pms.board.service.room.type"].create(
            {
                "pms_room_type_id": self.room_type_double.id,
                "pms_board_service_id": self.board_service1.id,
            }
        )

        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=3),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "board_service_room_id": self.board_service_room_type1.id,
                "sale_channel_origin_id": self.sale_channel_door.id,
            }
        )
        # ACT
        self.reservation.sale_channel_origin_id = self.sale_channel_mail

        # ASSERT
        self.assertIn(
            self.reservation.sale_channel_origin_id,
            self.reservation.service_ids.sale_channel_origin_id,
            "sale_channel_origin_id of service must be the same that its reservation ",
        )

    @freeze_time("2002-02-01")
    def test_reservation_sale_origin_in_service(self):
        """
        When a reservation is created with service, the sale_channel_origin_id
        is indicated in reservation. Therefore, the service takes
        the sale_channel_origin of its reservation

        Reservation --> sale_channel_origin_id = Door
                    |
                    --> service.sale_channel_origin_id? It must be Door
        """
        # ARRANGE
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                "is_extra_bed": True,
            }
        )

        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=2),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "sale_channel_origin_id": self.sale_channel_door.id,
            }
        )
        # ACT
        self.service1 = self.env["pms.service"].create(
            {
                "reservation_id": self.reservation.id,
                "product_id": self.product1.id,
                "is_board_service": False,
            }
        )
        # ASSERT
        self.assertEqual(
            self.reservation.sale_channel_origin_id,
            self.service1.sale_channel_origin_id,
            "sale_channel_origin of service must be the same as its reservation",
        )

    @freeze_time("2002-02-03")
    def test_origin_different_in_services_check_sale_channel_ids(self):
        """
        Check that sale_channel_ids is calculated well (in folio and
        reservation) when a reservation has services from different sale_channels

        Reservation --> sale_channel_origin = Door    sale_channel_ids = Door
                    |
                    --> service.sale_channel_origin = Door

        Add in reservation another service with sale_channel_origin = Phone, expected results:

        Reservation --> sale_channel_origin = Door    sale_channel_ids = Door, Phone
                    |
                    --> service[0].sale_channel_origin = Door
                    |
                    --> service[1].sale_channel_origin = Phone

        Reservation.folio_id.sale_channels = {Door, Phone}

        Check sale_channel_ids of reservation and its folio
        """
        # ARRANGE
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                "is_extra_bed": True,
            }
        )

        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=2),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "sale_channel_origin_id": self.sale_channel_door.id,
            }
        )
        # ACT
        self.service1 = self.env["pms.service"].create(
            {
                "reservation_id": self.reservation.id,
                "product_id": self.product1.id,
                "is_board_service": False,
            }
        )
        self.service2 = self.env["pms.service"].create(
            {
                "reservation_id": self.reservation.id,
                "product_id": self.product1.id,
                "is_board_service": False,
                "sale_channel_origin_id": self.sale_channel_phone.id,
            }
        )

        sale_channel_ids = [
            self.reservation.folio_id.sale_channel_ids,
            self.reservation.sale_channel_ids,
        ]

        expected_sale_channel_ids = self.reservation.service_ids.mapped(
            "sale_channel_origin_id"
        )

        # ASSERT
        for sale_channel in sale_channel_ids:
            with self.subTest(k=sale_channel):
                self.assertItemsEqual(
                    sale_channel,
                    expected_sale_channel_ids,
                    "sale_channel_ids must contain sale_channel_id of all board_service_lines",
                )

    @freeze_time("2002-02-16")
    def test_change_origin_service_not_change_reservation_origin(self):
        """
        When you change the sale_channel_origin_id of a service in a reservation
        that matched the origin of its reservation, if that reservation has reservation_lines
        with that sale_channel_id, it doesn't change the origin of reservation

        Reservation --> sale_channel_origin = Door
                    |
                    --> service.sale_channel_origin = Door

        Change sale_channel_origin of service to Phone, expected results:

        Reservation --> sale_channel_origin = Door    ----CHECKING THIS---
                    |
                    --> service.sale_channel_origin = Phone

        """
        # ARRANGE
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                "is_extra_bed": True,
            }
        )

        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=2),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "sale_channel_origin_id": self.sale_channel_door.id,
            }
        )

        self.service1 = self.env["pms.service"].create(
            {
                "reservation_id": self.reservation.id,
                "product_id": self.product1.id,
                "is_board_service": False,
            }
        )
        # ACT
        self.reservation.service_ids.sale_channel_origin_id = self.sale_channel_phone.id
        # ASSERT
        self.assertNotEqual(
            self.reservation.sale_channel_origin_id,
            self.reservation.service_ids.sale_channel_origin_id,
            """sale_channel_origin_id mustn't match
            with sale_channel_origin_id of its reservation""",
        )

    @freeze_time("2002-02-23")
    def test_change_origin_in_services_check_sale_channel_ids(self):
        """
        Check that sale_channel_ids is calculated well (in folio and
        reservation) when a service of a reservation change its sale_channel_origin

        Reservation --> sale_channel_origin = Door    sale_channel_ids = Door
                    |
                    --> service.sale_channel_origin = Door

        Change sale_channel_origin of service to Mail, expected results:

        Reservation --> sale_channel_origin = Door
                    --> sale_channel_ids = Door, Mail -----CHECKING THIS----
                    |
                    --> service.sale_channel_origin = Mail

        Reservation.folio_id.sale_channels = {Door, Mail} -----CHECKING THIS----

        Check sale_channel_ids of reservation and its folio
        """
        # ARRANGE
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                "is_extra_bed": True,
            }
        )

        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=2),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "sale_channel_origin_id": self.sale_channel_door.id,
            }
        )

        self.service1 = self.env["pms.service"].create(
            {
                "reservation_id": self.reservation.id,
                "product_id": self.product1.id,
                "is_board_service": False,
            }
        )

        # ACT
        self.service1.sale_channel_origin_id = self.sale_channel_mail

        sale_channel_ids = [
            self.reservation.folio_id.sale_channel_ids.ids,
            self.reservation.sale_channel_ids.ids,
        ]

        expected_sale_channel_ids = [
            self.sale_channel_door.id,
            self.sale_channel_mail.id,
        ]

        # ASSERT
        for sale_channel in sale_channel_ids:
            with self.subTest(k=sale_channel):
                self.assertItemsEqual(
                    sale_channel,
                    expected_sale_channel_ids,
                    "sale_channel_ids must contain sale_channel_origin_id of all services",
                )

    @freeze_time("2002-02-25")
    def test_change_origin_in_reservation_change_origin_service(self):
        """
        Check that when change sale_channel_origin of a reservation, sale_channel_origin
        of services that match with the origin changed, change too

        Service --> sale_channel_origin_id = Door   sale_channel_ids = {Door, Phone}
                |
                --> service[0].sale_channel_id = Door
                |
                --> service[1].sale_channel_id = Phone

        Change service origin to mail, expected results:
        Reservation --> sale_channel_origin_id = Mail   sale_channel_ids = {Mail, Phone}
                |
                --> service[0].sale_channel_id = Mail  -----------CHECKING THIS---
                |
                --> service[1].sale_channel_id = Phone
        """
        # ARRANGE
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                "is_extra_bed": True,
            }
        )

        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=2),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "sale_channel_origin_id": self.sale_channel_door.id,
            }
        )

        self.service1 = self.env["pms.service"].create(
            {
                "reservation_id": self.reservation.id,
                "product_id": self.product1.id,
                "is_board_service": False,
            }
        )
        self.service2 = self.env["pms.service"].create(
            {
                "reservation_id": self.reservation.id,
                "product_id": self.product1.id,
                "is_board_service": False,
                "sale_channel_origin_id": self.sale_channel_phone.id,
            }
        )

        # ACT
        self.reservation.sale_channel_origin_id = self.sale_channel_mail

        # ASSERT
        self.assertIn(
            self.reservation.sale_channel_origin_id,
            self.reservation.service_ids.mapped("sale_channel_origin_id"),
            "sale_channel_origin_id of that service should be changed",
        )

    @freeze_time("2002-03-29")
    def test_change_origin_in_reservation_no_change_origin_service(self):
        """
        Check that when change sale_channel_origin of a reservation, sale_channel_origin
        of services that don't match with the origin changed don't change

        Service --> sale_channel_origin_id = Door   sale_channel_ids = {Door, Phone}
                |
                --> service[0].sale_channel_id = Door
                |
                --> service[1].sale_channel_id = Phone

        Change service origin to mail, expected results:
        Reservation --> sale_channel_origin_id = Mail   sale_channel_ids = {Mail, Phone}
                |
                --> service[0].sale_channel_id = Mail
                |
                --> service[1].sale_channel_id = Phone -----------CHECKING THIS---
        """
        # ARRANGE
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                "is_extra_bed": True,
            }
        )

        self.reservation = self.env["pms.reservation"].create(
            {
                "checkin": fields.date.today(),
                "checkout": fields.date.today() + datetime.timedelta(days=2),
                "room_type_id": self.room_type_double.id,
                "partner_id": self.partner1.id,
                "pms_property_id": self.pms_property1.id,
                "pricelist_id": self.pricelist1.id,
                "sale_channel_origin_id": self.sale_channel_door.id,
            }
        )

        self.service1 = self.env["pms.service"].create(
            {
                "reservation_id": self.reservation.id,
                "product_id": self.product1.id,
                "is_board_service": False,
            }
        )
        self.service2 = self.env["pms.service"].create(
            {
                "reservation_id": self.reservation.id,
                "product_id": self.product1.id,
                "is_board_service": False,
                "sale_channel_origin_id": self.sale_channel_phone.id,
            }
        )

        # ACT
        self.reservation.sale_channel_origin_id = self.sale_channel_mail

        # ASSERT
        self.assertIn(
            self.sale_channel_phone,
            self.reservation.service_ids.mapped("sale_channel_origin_id"),
            "sale_channel_origin_id of that service shouldn't be changed",
        )

    @freeze_time("2002-03-01")
    def test_new_service_in_folio_sale_channel_origin(self):
        """
        Check that when a service is created within a folio already created,
        this service will use the sale_channel_origin_id of the folio as
        its sale_channel_origin_id

        Folio ----> sale_channel_origin_id = Door
              |
              ----> service.sale_channel_origin_id? It must be Door
        """
        # ARRANGE
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                "is_extra_bed": True,
            }
        )
        self.folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_name": self.partner1.name,
                "sale_channel_origin_id": self.sale_channel_door.id,
            }
        )
        # ACT
        self.service1 = self.env["pms.service"].create(
            {
                "product_id": self.product1.id,
                "is_board_service": False,
                "folio_id": self.folio1.id,
            }
        )
        # ASSERT
        self.assertEqual(
            self.folio1.sale_channel_origin_id,
            self.service1.sale_channel_origin_id,
            "Service that is just created must have its folio sale_channel_origin",
        )

    @freeze_time("2002-03-03")
    def test_change_origin_folio_change_origin_one_service(self):
        """
        Check that when a folio has a service, changing the sale_channel_origin
        of folio changes sale_channel_origin of it service

        Folio ----> sale_channel_origin_id = Door
              |
              ----> service.sale_channel_origin_id = Door

        Change sale_channel_origin of folio to Mail
         Folio ----> sale_channel_origin_id = Mail
              |
              ----> service.sale_channel_origin_id = Mail ---CHECKING THIS---
        """
        # ARRANGE
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                "is_extra_bed": True,
            }
        )
        self.folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_name": self.partner1.name,
                "sale_channel_origin_id": self.sale_channel_door.id,
            }
        )

        self.service1 = self.env["pms.service"].create(
            {
                "product_id": self.product1.id,
                "is_board_service": False,
                "folio_id": self.folio1.id,
            }
        )
        # ACT
        self.folio1.sale_channel_origin_id = self.sale_channel_mail.id

        # ASSERT
        self.assertEqual(
            self.folio1.sale_channel_origin_id,
            self.service1.sale_channel_origin_id,
            "Service must have equal sale_channel_origin than folio",
        )

    @freeze_time("2002-03-05")
    def test_change_origin_service_change_origin_folio(self):
        """
        When a folio has only one service, when changing the service sale_channel_origin
        folio.sale_channel_origin will also change

        Folio ----> sale_channel_origin_id = Door
              |
              ----> service.sale_channel_origin_id = Door

        Change sale_channel_origin of service to Mail
         Folio ----> sale_channel_origin_id = Mail ---CHECKING THIS---
              |
              ----> service.sale_channel_origin_id = Mail
        """
        # ARRANGE
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                "is_extra_bed": True,
            }
        )
        self.folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_name": self.partner1.name,
                "sale_channel_origin_id": self.sale_channel_door.id,
            }
        )

        self.service1 = self.env["pms.service"].create(
            {
                "product_id": self.product1.id,
                "is_board_service": False,
                "folio_id": self.folio1.id,
            }
        )
        # ACT
        self.service1.sale_channel_origin_id = self.sale_channel_mail.id

        # ASSERT
        self.assertEqual(
            self.folio1.sale_channel_origin_id,
            self.service1.sale_channel_origin_id,
            "Service must have equal sale_channel_origin than folio",
        )

    @freeze_time("2002-03-07")
    def test_folio_sale_channels_with_service_different_origins(self):
        """
        Check that on a folio with services with differents sale_channel_origin
        the sale_channel_ids of folio are calculated well.
        In this case sale_channel_ids must be formed by sale_channel_origin of its
        services

        Folio ----> sale_channel_origin_id = Door
              ----> sale_cahnnel_ids = {Door, Mail} ---CHECKING THIS----
              |
              ----> service.sale_channel_origin_id = Door
              |
              ----> service.sale_channel_origin_id = Mail
        """
        # ARRANGE
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                "is_extra_bed": True,
            }
        )
        self.folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_name": self.partner1.name,
                "sale_channel_origin_id": self.sale_channel_door.id,
            }
        )
        # ACT
        self.service1 = self.env["pms.service"].create(
            {
                "product_id": self.product1.id,
                "is_board_service": False,
                "folio_id": self.folio1.id,
            }
        )
        self.service2 = self.env["pms.service"].create(
            {
                "product_id": self.product1.id,
                "is_board_service": False,
                "folio_id": self.folio1.id,
                "sale_channel_origin_id": self.sale_channel_mail.id,
            }
        )

        expected_sale_channels = self.folio1.service_ids.mapped(
            "sale_channel_origin_id"
        )

        # ASSERT
        self.assertEqual(
            self.folio1.sale_channel_ids,
            expected_sale_channels,
            "sale_channel_ids must be the set of sale_channel_origin of its services",
        )

    @freeze_time("2002-03-10")
    def test_change_origin_folio_change_origin_service(self):
        """
        Check that when a folio has several services with different sale_channel_origin_id
        and change sale_channel_origin_id of folio, only changes origin of those services that
        match with the sale_channel_origin changed

        Folio ----> sale_channel_origin_id = Door
              |
              ----> service[0].sale_channel_origin_id = Door
              |
              ----> service[1].sale_channel_origin_id = Mail

        Change origin of folio to Phone, expected results:
        Folio ----> sale_channel_origin_id = Phone
              |
              ----> service[0].sale_channel_origin_id = Phone ---CHECKIN THIS---
              |
              ----> service[1].sale_channel_origin_id = Mail
        """
        # ARRANGE
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                "is_extra_bed": True,
            }
        )
        self.folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_name": self.partner1.name,
                "sale_channel_origin_id": self.sale_channel_door.id,
            }
        )

        self.service1 = self.env["pms.service"].create(
            {
                "product_id": self.product1.id,
                "is_board_service": False,
                "folio_id": self.folio1.id,
            }
        )
        self.service2 = self.env["pms.service"].create(
            {
                "product_id": self.product1.id,
                "is_board_service": False,
                "folio_id": self.folio1.id,
                "sale_channel_origin_id": self.sale_channel_mail.id,
            }
        )
        # ACT
        self.folio1.sale_channel_origin_id = self.sale_channel_phone.id

        # ASSERT
        self.assertIn(
            self.sale_channel_phone,
            self.folio1.service_ids.mapped("sale_channel_origin_id"),
            "sale_channel_origin_id of that service must be changed",
        )

    @freeze_time("2002-03-13")
    def test_change_origin_folio_no_change_origin_service(self):
        """
        Check that when a folio has several services with different sale_channel_origin_id
        and change sale_channel_origin_id of folio, only changes origin of those services that
        match with the sale_channel_origin changed. Then services that didn't initially
        match with sale_channel_origin of folio shouldn't have changed

        Folio ----> sale_channel_origin_id = Door
              |
              ----> service[0].sale_channel_origin_id = Door
              |
              ----> service[1].sale_channel_origin_id = Mail

        Change origin of folio to Phone, expected results:
        Folio ----> sale_channel_origin_id = Phone
              |
              ----> service[0].sale_channel_origin_id = Phone
              |
              ----> service[1].sale_channel_origin_id = Mail ---CHECKIN THIS---
        """
        # ARRANGE
        self.product1 = self.env["product.product"].create(
            {
                "name": "Test Product 1",
                "per_day": True,
                "consumed_on": "after",
                "is_extra_bed": True,
            }
        )
        self.folio1 = self.env["pms.folio"].create(
            {
                "pms_property_id": self.pms_property1.id,
                "partner_name": self.partner1.name,
                "sale_channel_origin_id": self.sale_channel_door.id,
            }
        )

        self.service1 = self.env["pms.service"].create(
            {
                "product_id": self.product1.id,
                "is_board_service": False,
                "folio_id": self.folio1.id,
            }
        )
        self.service2 = self.env["pms.service"].create(
            {
                "product_id": self.product1.id,
                "is_board_service": False,
                "folio_id": self.folio1.id,
                "sale_channel_origin_id": self.sale_channel_mail.id,
            }
        )
        # ACT
        self.folio1.sale_channel_origin_id = self.sale_channel_phone.id

        # ASSERT
        self.assertIn(
            self.sale_channel_mail,
            self.folio1.service_ids.mapped("sale_channel_origin_id"),
            "sale_channel_origin_id of that service mustn't be changed",
        )
