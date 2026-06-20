# Copyright (c) 2024 Gray Matter Logic
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from psycopg2 import IntegrityError

from odoo.tests.common import mute_logger

from .common import PmsBaseCase


class TestPmsTeam(PmsBaseCase):
    """Tests for pms.team model."""

    def test_create_team(self):
        """A team can be created with a name."""
        team = self.env["pms.team"].create({"name": "North Team"})
        self.assertEqual(team.name, "North Team")
        self.assertEqual(team.property_count, 0)

    def test_property_count_zero_initially(self):
        """A new team has property_count of 0."""
        team = self.env["pms.team"].create({"name": "Empty Team"})
        self.assertEqual(team.property_count, 0)

    def test_property_count_increments(self):
        """property_count reflects the number of properties in the team."""
        team = self.env["pms.team"].create({"name": "Count Team"})
        self.assertEqual(team.property_count, 0)
        self.env["pms.property"].create(
            {
                "name": "Prop In Team",
                "owner_id": self.owner.id,
                "tz": "UTC",
                "team_id": team.id,
            }
        )
        team.invalidate_recordset()
        self.assertEqual(team.property_count, 1)

    def test_property_count_multiple(self):
        """property_count handles multiple properties."""
        team = self.env["pms.team"].create({"name": "Multi Team"})
        for i in range(3):
            self.env["pms.property"].create(
                {
                    "name": f"Prop {i}",
                    "owner_id": self.owner.id,
                    "tz": "UTC",
                    "team_id": team.id,
                }
            )
        team.invalidate_recordset()
        self.assertEqual(team.property_count, 3)

    def test_unique_name_constraint(self):
        """Creating two teams with the same name raises an error."""
        self.env["pms.team"].create({"name": "Unique Team"})
        with mute_logger("odoo.sql_db"), self.assertRaises(IntegrityError):
            with self.env.cr.savepoint():
                self.env["pms.team"].create({"name": "Unique Team"})

    def test_default_stages_on_creation(self):
        """A new team gets the default stages automatically."""
        # Ensure at least one default stage exists
        default_stage = self.env["pms.stage"].search(
            [("is_default", "=", True)], limit=1
        )
        if not default_stage:
            default_stage = self.env["pms.stage"].create(
                {
                    "name": "Test Default",
                    "stage_type": "property",
                    "is_default": True,
                }
            )
        team = self.env["pms.team"].create({"name": "Staged Team"})
        self.assertIn(default_stage, team.stage_ids)

    def test_company_defaults_to_current(self):
        """A new team defaults to the current company."""
        team = self.env["pms.team"].create({"name": "Company Team"})
        self.assertEqual(team.company_id, self.env.company)

    def test_sequence_ordering(self):
        """Teams with lower sequence appear first."""
        t1 = self.env["pms.team"].create({"name": "First Team", "sequence": 1})
        t2 = self.env["pms.team"].create({"name": "Second Team", "sequence": 10})
        teams = self.env["pms.team"].search(
            [("name", "in", ["First Team", "Second Team"])]
        )
        self.assertEqual(teams[0], t1)
        self.assertEqual(teams[1], t2)
