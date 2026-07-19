# Copyright 2026 Commit [Sun]
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Initialize assignment_sequence with the current display sequence.
    # If the column already exists (e.g. created manually ahead of this
    # migration), keep the values already set.
    if not openupgrade.column_exists(env.cr, "pms_room", "assignment_sequence"):
        env.cr.execute(
            """
            ALTER TABLE pms_room
            ADD COLUMN assignment_sequence integer
            """
        )
        env.cr.execute(
            """
            UPDATE pms_room
            SET assignment_sequence = sequence
            """
        )
