from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Copy allowed_pms_payments from journals to their inbound payment method lines
    old_column = openupgrade.get_legacy_name("allowed_pms_payments")
    env.cr.execute(
        f"""
        UPDATE account_payment_method_line apml
        SET allowed_on_pms = TRUE
        FROM account_journal aj
        WHERE apml.journal_id = aj.id
          AND aj.{old_column} = TRUE
          AND apml.id IN (
              SELECT apml2.id
              FROM account_payment_method_line apml2
              JOIN account_payment_method apm ON apm.id = apml2.payment_method_id
              WHERE apm.payment_type = 'inbound'
          )
        """
    )
