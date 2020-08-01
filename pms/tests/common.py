##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
from datetime import timedelta

from odoo import api, fields
from odoo.tests import common
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)


class TestHotel(common.SavepointCase):
    @classmethod
    def _init_mock_hotel(cls):
        return True

    def create_folio(self, creator, partner):
        # Create Folio
        folio = (
            self.env["hotel.folio"].sudo(creator).create({"partner_id": partner.id,})
        )
        self.assertTrue(folio, "Can't create folio")
        return folio

    def create_reservation(
        self, creator, folio, checkin, checkout, room, resname, adults=1, children=0
    ):
        # Create Reservation (Special Room)
        reservation = (
            self.env["hotel.reservation"]
            .sudo(creator)
            .create(
                {
                    "name": resname,
                    "adults": adults,
                    "children": children,
                    "checkin": checkin.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    "checkout": checkout.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                    "folio_id": folio.id,
                    "room_type_id": room.price_room_type.id,
                    "product_id": room.product_id.id,
                }
            )
        )
        self.assertTrue(reservation, "Hotel Calendar can't create a new reservation!")

        # Create Reservation Lines + Update Reservation Price
        # days_diff = date_utils.date_diff(checkin, checkout, hours=False)
        # res = reservation.sudo(creator).prepare_reservation_lines(
        #     checkin.strftime(DEFAULT_SERVER_DATETIME_FORMAT), days_diff)
        # reservation.sudo(creator).write({
        #     'reservation_lines': res['commands'],
        #     'price_unit': res['total_price'],
        # })

        return reservation

    @classmethod
    def setUpClass(cls):
        super(TestHotel, cls).setUpClass()

        cls._init_mock_hotel()

        # Create Tests Records
        cls.main_hotel_property = cls.env.ref("hotel.main_hotel_property")
        cls.demo_hotel_property = cls.env.ref("hotel.demo_hotel_property")

        cls.room_type_0 = cls.env.ref("hotel.hotel_room_type_0")
        cls.room_type_1 = cls.env.ref("hotel.hotel_room_type_1")
        cls.room_type_2 = cls.env.ref("hotel.hotel_room_type_2")
        cls.room_type_3 = cls.env.ref("hotel.hotel_room_type_3")

        cls.demo_room_type_0 = cls.env.ref("hotel.demo_hotel_room_type_0")
        cls.demo_room_type_1 = cls.env.ref("hotel.demo_hotel_room_type_1")

        cls.room_0 = cls.env.ref("hotel.hotel_room_0")
        cls.room_1 = cls.env.ref("hotel.hotel_room_1")
        cls.room_2 = cls.env.ref("hotel.hotel_room_2")
        cls.room_3 = cls.env.ref("hotel.hotel_room_3")
        cls.room_4 = cls.env.ref("hotel.hotel_room_4")
        cls.room_5 = cls.env.ref("hotel.hotel_room_5")
        cls.room_6 = cls.env.ref("hotel.hotel_room_6")

        cls.list0 = cls.env.ref("product.list0")
        cls.list1 = cls.env["product.pricelist"].create(
            {"name": "Test Pricelist", "pricelist_type": ""}
        )
