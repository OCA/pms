from openupgradelib import openupgrade

_rename_fields = [
    (
        "pms.checkin.partner",
        "pms_checkin_partner",
        "residence_street",
        "street",
    ),
    (
        "pms.checkin.partner",
        "pms_checkin_partner",
        "residence_street2",
        "street2",
    ),
    (
        "pms.checkin.partner",
        "pms_checkin_partner",
        "residence_zip",
        "zip",
    ),
    (
        "pms.checkin.partner",
        "pms_checkin_partner",
        "residence_city",
        "city",
    ),
    (
        "pms.checkin.partner",
        "pms_checkin_partner",
        "residence_country_id",
        "country_id",
    ),
    (
        "pms.checkin.partner",
        "pms_checkin_partner",
        "residence_state_id",
        "state_id",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    for model, table, oldfield, newfield in _rename_fields:
        if not openupgrade.column_exists(env.cr, table, oldfield):
            continue
        openupgrade.rename_fields(env, [(model, table, oldfield, newfield)])
