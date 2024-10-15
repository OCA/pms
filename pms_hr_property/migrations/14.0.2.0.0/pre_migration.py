from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE pms_ rl
        SET sale_channel_id = r.sale_channel_origin_id
        FROM pms_reservation r
        WHERE r.id = rl.reservation_id
        """,
    )

    openupgrade.logged_query(
        env.cr,
        """
        UPDATE pms_service ser
        SET sale_channel_origin_id = fol.sale_channel_origin_id
        FROM pms_folio fol
        WHERE fol.id = ser.folio_id
        """,
    )
