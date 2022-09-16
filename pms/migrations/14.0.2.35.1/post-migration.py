from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE pms_reservation
        SET to_send_confirmation_mail = False,
        to_send_cancelation_mail = False,
        to_send_exit_mail = False,
        to_send_modification_mail = False;
        """,
    )
