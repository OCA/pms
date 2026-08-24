# Copyright 2026 Commit [Sun]
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from unittest.mock import patch

from odoo import fields
from odoo.tests import common

from odoo.addons.multi_pms_properties import _description_domain


class TestViewCheckPmsProperties(common.TransactionCase):
    """Views must keep the property field available for every group combination.

    ``multi_pms_properties`` injects a domain into every relational field declared
    with ``check_pms_properties=True``, and that domain refers to the property
    field of the model (``pms_property_ids`` or ``pms_property_id``). Odoo refuses
    to validate a view where a field used in the domain of another field is
    restricted to a narrower group, so restricting the property field with
    ``groups`` breaks the whole view, and with it the module load.

    The injection only happens when ``multi_pms_properties`` is loaded through
    ``server_wide_modules``, which is not the case while running tests. The patch
    is therefore applied explicitly here, so the check reproduces a real
    deployment instead of silently passing.
    """

    # Views showing fields whose injected domain refers to the property field
    VIEWS = [
        "pms.product_pricelist_view_form",
        "pms.product_pricelist_item_view_form",
        "pms.product_template_view_form",
        "pms.res_partner_view_form",
    ]

    def test_views_validate_with_injected_property_domain(self):
        with patch.object(
            fields._Relational, "check_pms_properties", False, create=True
        ), patch.object(
            fields._Relational, "_description_domain", _description_domain, create=True
        ):
            for xml_id in self.VIEWS:
                with self.subTest(view=xml_id):
                    self.env.ref(xml_id)._check_xml()
