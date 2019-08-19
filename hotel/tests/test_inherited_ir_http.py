# -*- coding: utf-8 -*-
from .common import TestHotel


class TestInheritedIrHttp(TestHotel):

    def test_user_hotel_company(self):
        admin_user = self.env.ref('base.user_root')
        self.assertTrue(admin_user.hotel_id.company_id in admin_user.company_ids,
                        "Wrong hotel and company access settings for %s" % admin_user.name)

