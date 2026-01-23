from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if env["ir.model.data"].search(
        [("module", "=", "pms"), ("name", "=", "document_type_passport")], limit=1
    ):
        openupgrade.rename_xmlids(
            env.cr,
            [
                (
                    "pms.document_type_passport",
                    "pms_partner_identification.document_type_passport",
                ),
            ],
        )
    if env["ir.model.data"].search(
        [("module", "=", "pms"), ("name", "=", "document_type_other")], limit=1
    ):
        openupgrade.rename_xmlids(
            env.cr,
            [
                (
                    "pms.document_type_other",
                    "pms_partner_identification.document_type_other",
                ),
            ],
        )

    if not openupgrade.is_module_installed(env.cr, "pms_l10n_es"):
        return
    if env["ir.model.data"].search(
        [("module", "=", "pms_l10n_es"), ("name", "=", "document_type_dni")], limit=1
    ):
        openupgrade.rename_xmlids(
            env.cr,
            [
                (
                    "pms_l10n_es.document_type_dni",
                    "pms_partner_identification.document_type_national_id",
                ),
            ],
        )
        env.ref("pms_partner_identification.document_type_national_id").write(
            {"country_ids": [(6, 0, [])]}
        )

        res_id = env.ref("pms_partner_identification.document_type_national_id")
        base_lang = env.user.lang or "en_US"
        env.cr.execute(
            """
        UPDATE res_partner_id_category
        SET name = jsonb_build_object(%s, %s)
        WHERE id = %s
            """,
            (base_lang, "National ID", res_id),
        )
