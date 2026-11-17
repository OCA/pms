# Copyright (c) 2024 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError

from .common import PmsBaseCase


class TestPmsStage(PmsBaseCase):
    """Tests for pms.stage model."""

    def _make_stage(self, name, color="#FFFFFF", **kw):
        return self.env["pms.stage"].create(
            {
                "name": name,
                "stage_type": "property",
                "custom_color": color,
                **kw,
            }
        )

    def test_create_stage(self):
        """A stage can be created with mandatory fields."""
        stage = self._make_stage("In Renovation")
        self.assertEqual(stage.name, "In Renovation")
        self.assertEqual(stage.stage_type, "property")
        self.assertFalse(stage.is_closed)
        self.assertFalse(stage.is_default)

    def test_valid_hex_color(self):
        """A valid hex color passes the constraint."""
        stage = self._make_stage("Green Stage", color="#00FF00")
        self.assertEqual(stage.custom_color, "#00FF00")

    def test_invalid_hex_color_no_hash(self):
        """A color without '#' raises ValidationError."""
        with self.assertRaises(ValidationError):
            self._make_stage("Bad Color", color="FF0000")

    def test_invalid_hex_color_wrong_length(self):
        """A color with wrong length raises ValidationError."""
        with self.assertRaises(ValidationError):
            self._make_stage("Short Color", color="#FFF")

    def test_default_stage_flag(self):
        """is_default can be set and is used by _default_stages."""
        stage = self._make_stage("Default Stage", is_default=True)
        self.assertTrue(stage.is_default)
        default_stages = self.env["pms.stage"].search([("is_default", "=", True)])
        self.assertIn(stage, default_stages)

    def test_closed_stage_flag(self):
        """is_closed marks a stage as a closing stage."""
        stage = self._make_stage("Closed Stage", is_closed=True)
        self.assertTrue(stage.is_closed)

    def test_fold_flag(self):
        """fold can be set on a stage."""
        stage = self._make_stage("Folded Stage", fold=True)
        self.assertTrue(stage.fold)

    def test_default_stages_used_by_team(self):
        """A new team receives the default stages."""
        self._make_stage("My Default", is_default=True)
        team = self.env["pms.team"].create({"name": "Stage Test Team"})
        default_stages = self.env["pms.stage"].search([("is_default", "=", True)])
        for stage in default_stages:
            self.assertIn(stage, team.stage_ids)

    def test_stage_sequence_ordering(self):
        """Stages are retrieved in sequence order."""
        s1 = self._make_stage("First", sequence=1)
        s2 = self._make_stage("Second", sequence=2)
        stages = self.env["pms.stage"].search(
            [("name", "in", ["First", "Second"])], order="sequence"
        )
        self.assertEqual(stages[0], s1)
        self.assertEqual(stages[1], s2)
