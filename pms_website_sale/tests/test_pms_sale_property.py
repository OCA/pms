# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from odoo.addons.base.tests.common import HttpCaseWithUserPortal


@tagged("post_install", "-at_install")
class TestWebsiteSaleCartRecovery(HttpCaseWithUserPortal):
    def test_01_property_page(self):
        self.start_tour("/", "property_load_homepage", login="portal")
        self.env["pms.property"].create(
            {
                "name": "Property 1",
                "website_published": True,
                "owner_id": self.env.ref("base.res_partner_12").id,
                "no_of_guests": 2,
            }
        )
        self.env["pms.property"].create(
            {
                "name": "Property 2",
                "website_published": True,
                "owner_id": self.env.ref("base.res_partner_12").id,
                "no_of_guests": 2,
            }
        )
        self.env["pms.property"].create(
            {
                "name": "Property 3",
                "website_published": True,
                "owner_id": self.env.ref("base.res_partner_12").id,
                "no_of_guests": 2,
            }
        )
        self.env["pms.property"].create(
            {
                "name": "Property 4",
                "website_published": True,
                "owner_id": self.env.ref("base.res_partner_12").id,
                "no_of_guests": 2,
            }
        )
        self.start_tour("/", "property_search_homepage")
