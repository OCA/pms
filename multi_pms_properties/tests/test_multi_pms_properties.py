# Copyright 2021 Eric Antones
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common

from .common import CommonPMS


@common.tagged("-at_install", "post_install")
class TestMultiPMSProperties(CommonPMS):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        model_classes = [cls.parent_tester_pms, cls.child_tester_pms]
        # setup_test_model(cls.env, model_classes)
        for mdl_cls in model_classes:
            tester_model = cls.env["ir.model"].search([("model", "=", mdl_cls._name)])
            # Access record
            cls.env["ir.model.access"].create(
                {
                    "name": f"access.{mdl_cls._name}",
                    "model_id": tester_model.id,
                    "perm_read": 1,
                    "perm_write": 1,
                    "perm_create": 1,
                    "perm_unlink": 1,
                }
            )

    def test_exist_attribute(self):
        self.parent_tester_pms.create({"name": "parent test"})
