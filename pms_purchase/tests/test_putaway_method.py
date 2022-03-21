# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.tests.common import TransactionCase


class TestPutawayMethod(TransactionCase):

    # Check if "fixed" is a valid putaway method
    def test_02_putaway_methods(self):
        field_method = self.env["stock.putaway.rule"]._fields.get("method")
        self.assertIn("move_to_property", field_method.get_values(self.env))
