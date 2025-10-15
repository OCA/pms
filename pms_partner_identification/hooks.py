from openupgradelib import openupgrade

from odoo import SUPERUSER_ID, api


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if env["ir.model.data"].search(
        [("module", "=", "pms"), ("name", "=", "document_type_passport")], limit=1
    ):
        openupgrade.rename_xmlids(
            cr,
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
            cr,
            [
                (
                    "pms.document_type_other",
                    "pms_partner_identification.document_type_other",
                ),
            ],
        )

    if not openupgrade.is_module_installed(cr, "pms_l10n_es"):
        return
    if env["ir.model.data"].search(
        [("module", "=", "pms_l10n_es"), ("name", "=", "document_type_dni")], limit=1
    ):
        openupgrade.rename_xmlids(
            cr,
            [
                (
                    "pms_l10n_es.document_type_dni",
                    "pms_partner_identification.document_type_national_id",
                ),
            ],
        )
        res_id = env.ref("pms_partner_identification.document_type_national_id").id
        base_lang = env.user.lang or "en_US"
        cr.execute(
            """
        UPDATE res_partner_id_category
        SET name = jsonb_build_object(%s, %s)
        WHERE id = %s
            """,
            (base_lang, "National ID", res_id),
        )


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    if env["ir.model.data"].search(
        [
            ("module", "=", "pms_partner_identification"),
            ("name", "=", "document_type_national_id"),
        ],
        limit=1,
    ):
        env.ref("pms_partner_identification.document_type_national_id").write(
            {"country_ids": [(6, 0, [])]}
        )
