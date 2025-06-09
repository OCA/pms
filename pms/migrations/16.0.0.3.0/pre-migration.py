from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE res_partner_id_category
        SET active = FALSE
        WHERE id IN (
            select res_id from ir_model_data
            WHERE module = 'pms' AND name in
            ('document_type_driving_license',
             'document_type_identification_document',
             'document_type_european_residence')
        )
        """,
    )
