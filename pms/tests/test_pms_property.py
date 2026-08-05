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
