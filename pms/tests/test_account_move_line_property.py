# Copyright 2026 Commit [Sun]
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tests import tagged

from .common import TestPms


@tagged("post_install", "-at_install")
class TestAccountMoveLineProperty(TestPms):
    """A journal item belongs to the property of its move, at all times.

    The property of a move is not always known when its items are created: a
    payment collected at the desk gets its folio -- and with it its property --
    only when it is reconciled with the folio's invoice.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.account = cls.env["account.account"].create(
            {
                "name": "Property Test Account",
                "code": "PROPTEST",
                "account_type": "asset_current",
                "company_id": cls.company1.id,
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Property Test Journal",
                "code": "PRTST",
                "type": "general",
                "company_id": cls.company1.id,
            }
        )

    def _move(self):
        return (
            self.env["account.move"]
            .with_company(self.company1)
            .create(
                {
                    "move_type": "entry",
                    "journal_id": self.journal.id,
                    "line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": "Debit",
                                "account_id": self.account.id,
                                "debit": 10.0,
                                "credit": 0.0,
                            },
                        ),
                        (
                            0,
                            0,
                            {
                                "name": "Credit",
                                "account_id": self.account.id,
                                "debit": 0.0,
                                "credit": 10.0,
                            },
                        ),
                    ],
                }
            )
        )

    def test_lines_follow_the_property_of_their_move(self):
        move = self._move()
        self.assertFalse(move.pms_property_id)

        move.pms_property_id = self.pms_property1

        self.assertEqual(
            move.line_ids.mapped("pms_property_id"),
            self.pms_property1,
            "The journal items must take the property their move was given",
        )

    def test_the_consistency_check_passes_after_the_move_gets_a_property(self):
        """Without recomputing the items, they keep no property while their move
        has one. Nothing notices until the next write that touches a checked
        relational field -- which is every write account.payment makes when it
        synchronises its amount -- and then the entry is rejected as
        inconsistent, although the user never made it so."""
        move = self._move()
        move.pms_property_id = self.pms_property1

        move.line_ids._check_pms_properties()
