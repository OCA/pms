# Copyright (c) 2024 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import tagged

from odoo.addons.base.tests.common import HttpCaseWithUserPortal


@tagged("post_install", "-at_install")
class TestWebsiteSaleCartRecovery(HttpCaseWithUserPortal):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env["website"].get_current_website()
        cls.partner_owner = cls.env["res.partner"].create({"name": "Tour Owner"})

    def _create_published_property(self, name):
        return self.env["pms.property"].create(
            {
                "name": name,
                "owner_id": self.partner_owner.id,
                "website_id": self.website.id,
                "is_published": True,
                "website_published": True,
                "no_of_guests": 2,
            }
        )

    def test_01_property_page(self):
        self.start_tour("/", "property_load_homepage", login="portal")
        for idx in range(1, 5):
            self._create_published_property(f"Property {idx}")
        self.start_tour("/", "property_search_homepage")
