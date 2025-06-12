from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE res_partner_id_category
        SET name='{"en_US": "NIE"}',
        validation_code = replace(
            validation_code,
            '[''X'',''Y'']',
            '[''X'',''Y'' ''Z'']'
        )
        WHERE id IN (
            select res_id from ir_model_data
            WHERE module = 'pms_l10n_es' AND name = 'document_type_spanish_residence'
        )
        """,
    )
