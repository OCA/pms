# Copyright (c) 2024 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.pms_website_sale.controllers.website import PropertyTableCompute


@tagged("post_install", "-at_install")
class TestPropertyTableCompute(BaseCommon):
    def test_process_empty(self):
        rows = PropertyTableCompute().process([], ppg=20, ppr=4)
        self.assertEqual(rows, [])

    def test_process_single_item(self):
        product = object()
        rows = PropertyTableCompute().process([product], ppg=20, ppr=4)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0]["product"], product)

    def test_process_multiple_items(self):
        products = [object() for _ in range(4)]
        rows = PropertyTableCompute().process(products, ppg=20, ppr=2)
        placed = sum(1 for row in rows for cell in row if cell)
        self.assertEqual(placed, 4)
