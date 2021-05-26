from freezegun import freeze_time

from odoo.tests.common import SavepointCase

freeze_time("2000-02-02")


class TestPmsPayment(SavepointCase):
    def setUp(self):
        super(TestPmsPayment, self).setUp()
