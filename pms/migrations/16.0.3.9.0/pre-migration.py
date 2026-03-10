from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Rename old column to keep data for post-migration
    if openupgrade.column_exists(env.cr, "account_journal", "allowed_pms_payments"):
        openupgrade.rename_columns(
            env.cr,
            {"account_journal": [("allowed_pms_payments", None)]},
        )
