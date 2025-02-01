from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE pms_reservation
        ADD COLUMN IF NOT EXISTS folio_pending_amount DOUBLE PRECISION
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """UPDATE pms_reservation pr
        SET folio_pending_amount = pf.pending_amount
        FROM pms_folio pf
        WHERE pr.folio_id = pf.id
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE pms_folio
        ADD COLUMN IF NOT EXISTS currency_id INTEGER
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """UPDATE pms_folio pf
        SET currency_id = pr.currency_id
        FROM product_pricelist pr
        WHERE pf.pricelist_id = pr.id
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE pms_reservation_line
        ADD COLUMN IF NOT EXISTS currency_id INTEGER
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """UPDATE pms_reservation_line prl
        SET currency_id = pr.currency_id
        FROM pms_reservation pr
        WHERE prl.reservation_id = pr.id
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE pms_service
        ADD COLUMN IF NOT EXISTS pricelist_id INTEGER
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """UPDATE pms_service ps
        SET pricelist_id = coalesce(pr.pricelist_id, pf.pricelist_id)
        FROM pms_reservation pr, pms_folio pf
        WHERE pr.id = ps.reservation_id and pr.folio_id = pf.id
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE pms_service_line
        ADD COLUMN IF NOT EXISTS pricelist_id INTEGER
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """UPDATE pms_service_line psl
        SET pricelist_id = ps.pricelist_id
        FROM pms_service ps
        WHERE ps.id = psl.service_id
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE pms_reservation
        ADD COLUMN IF NOT EXISTS priority INTEGER
        """,
    )
