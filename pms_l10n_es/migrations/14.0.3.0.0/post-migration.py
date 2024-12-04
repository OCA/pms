import logging
import xml.etree.cElementTree as ET

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    _logger.info("Get commuication_ids from soap process response...")
    for ses_communication in env["pms.ses.communication"].search(
        [
            ("state", "=", "processed"),
            ("entity", "=", "RH"),
            ("operation", "=", "A"),
        ]
    ):
        root = ET.fromstring(ses_communication.response_query_status_soap)
        ses_communication.communication_id = root.find(".//codigoComunicacion").text
