# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import timedelta
from odoo.addons.hotel_calendar.tests.common import TestHotelCalendar
from odoo.addons.hotel import date_utils


class TestHotelReservations(TestHotelCalendar):

    def test_cancel_folio(self):
        now_utc_dt = date_utils.now()
