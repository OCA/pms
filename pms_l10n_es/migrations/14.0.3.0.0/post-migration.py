import logging
import xml.etree.cElementTree as ET

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    for ses_communication in env["pms.ses.communication"].search(
        [
            ("state", "=", "processed"),
            ("entity", "=", "RH"),
            ("operation", "=", "A"),
        ]
    ):
        root = ET.fromstring(ses_communication.response_query_status_soap)
        ses_communication.communication_id = root.find(".//codigoComunicacion").text
        ses_communication.batch_id = root.find(".//lote").text

    # Retry all communications type delete, set status to to_send
    env["pms.ses.communication"].search(
        [
            ("state", "in", ["processed", "error_processing"]),
            ("entity", "=", "RH"),
            ("operation", "=", "D"),
        ]
    ).write({"state": "to_send"})
