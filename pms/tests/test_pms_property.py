import datetime

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import INVALID_HOURS, TestPms


@tagged("post_install", "-at_install")
class TestPmsPropertyHours(TestPms):
    def test_default_hours_invalid_format(self):
        """
        Check that the property hours are a zero-padded 24h "HH:MM" string
        -------------
        Create a property for each hour that is not one, on both hour
        fields, this should throw an error. "8:00" is the value that
        broke production: the check accepted it and the consumers
        parsing the hour by position could not read it back.
        """
        for hour in INVALID_HOURS:
            for field in ("default_arrival_hour", "default_departure_hour"):
                with self.subTest(hour=hour, field=field), self.assertRaises(
                    ValidationError
                ):
                    self.env["pms.property"].create(
                        {
                            "name": "Property hour format",
                            "company_id": self.company1.id,
                            "default_pricelist_id": self.pricelist1.id,
                            field: hour,
                        }
                    )

    def test_hours_in_property_timezone(self):
        """
        Check that a property hour is read in the property's timezone,
        whoever reads it
        -------------
        On a property in Madrid (UTC+1 in January), 12:00 is 11:00 UTC for
        a user without timezone, as crons often run, and for a user in
        another timezone.
        """
        self.pms_property1.tz = "Europe/Madrid"
        for user_tz in (False, "Atlantic/Canary"):
            with self.subTest(user_tz=user_tz):
                self.env.user.tz = user_tz
                self.assertEqual(
                    self.pms_property1.datetime_from_hour_str(
                        datetime.date(2012, 1, 14), "12:00"
                    ),
                    datetime.datetime(2012, 1, 14, 11, 0),
                )
