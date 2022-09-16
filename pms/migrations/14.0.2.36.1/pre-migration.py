from openupgradelib import openupgrade

_field_renames = [
    ("pms.folio", "pms_folio", "channel_type_id", "sale_channel_origin_id"),
    ("pms.reservation", "pms_reservation", "channel_type_id", "sale_channel_origin_id"),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, _field_renames)
