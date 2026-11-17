# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestPutawayMethod(TransactionCase):
    def test_move_to_property_field(self):
        self.assertIn(
            "move_to_property",
            self.env["stock.putaway.rule"]._fields,
        )
