# Copyright 2021 Eric Antones
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo_test_helper import FakeModelLoader

from odoo.addons.base.tests.common import BaseCommon


class CommonPMS(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .multi_pms_properties_tester import (
            ChildTester,
            ParentTester,
        )

        cls.loader.update_registry(
            (
                ParentTester,
                ChildTester,
            )
        )

        cls.parent_tester_pms = cls.env[ParentTester._name]
        cls.child_tester_pms = cls.env[ChildTester._name]
