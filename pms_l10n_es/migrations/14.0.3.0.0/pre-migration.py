import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

_field_renames = [
    ("pms.ses.communication", "pms_ses_communication", "communication_id", "batch_id"),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, _field_renames)
