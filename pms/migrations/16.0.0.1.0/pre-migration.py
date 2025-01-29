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
        env.cr, """UPDATE pms_reservation pr
        SET folio_pending_amount = pf.pending_amount
        FROM pms_folio pf
        WHERE pr.folio_id = pf.id
        """
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE pms_folio
        ADD COLUMN IF NOT EXISTS currency_id INTEGER
        """,
    )
    openupgrade.logged_query(
        env.cr, """UPDATE pms_folio pf
        SET currency_id = pr.currency_id
        FROM product_pricelist pr
        WHERE pf.pricelist_id = pr.id
        """
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE pms_reservation_line
        ADD COLUMN IF NOT EXISTS currency_id INTEGER
        """,
    )
    openupgrade.logged_query(
        env.cr, """UPDATE pms_reservation_line prl
        SET currency_id = pr.currency_id
        FROM pms_reservation pr
        WHERE prl.reservation_id = pr.id
        """
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE pms_service
        ADD COLUMN IF NOT EXISTS pricelist_id INTEGER
        """,
    )
    openupgrade.logged_query(
        env.cr, """UPDATE pms_service ps
        SET pricelist_id = coalesce(pr.pricelist_id, pf.pricelist_id)
        FROM pms_reservation pr, pms_folio pf
        WHERE pr.id = ps.reservation_id and pr.folio_id = pf.id
        """
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE pms_service_line
        ADD COLUMN IF NOT EXISTS pricelist_id INTEGER
        """,
    )
    openupgrade.logged_query(
        env.cr, """UPDATE pms_service_line psl
        SET pricelist_id = ps.pricelist_id
        FROM pms_service ps
        WHERE ps.id = psl.service_id
        """
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE pms_reservation
        ADD COLUMN IF NOT EXISTS priority INTEGER
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE pms_reservation set priority =
        case when (to_assign = true or state in ('arrival_delayed', 'departure_delayed')) then 1
        when state = 'cancel' and folio_pending_amount > 0 then 2
        when state = 'cancel' and checkout >= CURRENT_DATE then 100
        when state = 'cancel' then 1000 * (CURRENT_DATE - checkout)
        when state = 'onboard' and folio_pending_amount > 0 then (checkout - CURRENT_DATE)
        when state = 'onboard' and folio_pending_amount <= 0 then 3 * (checkout - CURRENT_DATE)
        when state in ('draft', 'confirm') and (checkin - CURRENT_DATE) < 3 then 2 * (checkin - CURRENT_DATE)
        when state in ('draft', 'confirm') and (checkin - CURRENT_DATE) < 20 then 3 * (checkin - CURRENT_DATE)
        when state in ('draft', 'confirm') then 4 * (checkin - CURRENT_DATE)
        when state = 'done' and folio_pending_amount > 0 then 3
        when state = 'done' and (CURRENT_DATE - checkout) <= 1 then 6
        when state = 'done' and (CURRENT_DATE - checkout) < 15 then 5 * (CURRENT_DATE - checkout)
        when state = 'done' and (CURRENT_DATE - checkout) <= 90 then 10 * (CURRENT_DATE - checkout)
        when state = 'done' and (CURRENT_DATE - checkout) > 90 then 100 * (CURRENT_DATE - checkout)
        else 0 end
        """,
    )
