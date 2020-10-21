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

from odoo.tests import common

_logger = logging.getLogger(__name__)


class TestHotel(common.SavepointCase):
    @classmethod
    def _init_mock_hotel(cls):
        return True

    @classmethod
    def setUpClass(cls):
        super(TestHotel, cls).setUpClass()

        cls._init_mock_hotel()

        # Create Tests Records
        cls.main_hotel_property = cls.env.ref("pms.main_pms_property")
        cls.demo_hotel_property = cls.env.ref("pms.demo_pms_property")

        cls.room_type_0 = cls.env.ref("pms.pms_room_type_0")
        cls.room_type_1 = cls.env.ref("pms.pms_room_type_1")
        cls.room_type_2 = cls.env.ref("pms.pms_room_type_2")
        cls.room_type_3 = cls.env.ref("pms.pms_room_type_3")

        cls.demo_room_type_0 = cls.env.ref("pms.demo_pms_room_type_0")
        cls.demo_room_type_1 = cls.env.ref("pms.demo_pms_room_type_1")

        cls.room_0 = cls.env.ref("pms.pms_room_0")
        cls.room_1 = cls.env.ref("pms.pms_room_1")
        cls.room_2 = cls.env.ref("pms.pms_room_2")
        cls.room_3 = cls.env.ref("pms.pms_room_3")
        cls.room_4 = cls.env.ref("pms.pms_room_4")
        cls.room_5 = cls.env.ref("pms.pms_room_5")
        cls.room_6 = cls.env.ref("pms.pms_room_6")

        cls.list0 = cls.env.ref("product.list0")
        cls.list1 = cls.env["product.pricelist"].create(
            {"name": "Test Pricelist", "pricelist_type": ""}
        )
