# Copyright 2026 Commit [Sun]
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade

# children_occupying held the children taking a place in the room, apart from
# children, which held them all. Nothing kept both in sync, so a reservation
# could declare an occupying child without counting it in children. Those
# children are folded into children before the column goes away, or they would
# be lost.
_FOLD_CHILDREN_OCCUPYING = """
    UPDATE pms_reservation
    SET children = children_occupying
    WHERE children_occupying > COALESCE(children, 0)
"""


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(env.cr, "pms_reservation", "children_occupying"):
        openupgrade.logged_query(env.cr, _FOLD_CHILDREN_OCCUPYING)
        openupgrade.drop_columns(env.cr, [("pms_reservation", "children_occupying")])
