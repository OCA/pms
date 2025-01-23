import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """
    This migration script will update the list_price field of product.template
    with the value of the ir.pms.property record that has the highest value
    and amount field of pms.board.service.line
    with the value of the ir.pms.property record that has the highest value
    """
    _logger.info("Starting list_price migration from ir.pms.property")

    env.cr.execute(
        """
        WITH property_prices AS (
            SELECT DISTINCT ON (ip.record)
                ip.record,
                ip.value_float
            FROM ir_pms_property ip
            JOIN ir_model im ON ip.model_id = im.id
            JOIN ir_model_fields imf ON ip.field_id = imf.id
            WHERE im.model = 'product.template'
            AND imf.name = 'list_price'
            AND ip.value_float > 0
            ORDER BY ip.record, ip.value_float DESC
        )
        UPDATE product_template pt
        SET list_price = COALESCE(
            (SELECT value_float
             FROM property_prices pp
             WHERE pp.record = pt.id),
            1.0
        );
    """
    )

    _logger.info("Starting amount migration for pms.board.service.line")

    env.cr.execute(
        """
        WITH property_amounts AS (
            SELECT DISTINCT ON (ip.record)
                ip.record,
                ip.value_float
            FROM ir_pms_property ip
            JOIN ir_model im ON ip.model_id = im.id
            JOIN ir_model_fields imf ON ip.field_id = imf.id
            WHERE im.model = 'pms.board.service.line'
            AND imf.name = 'amount'
            AND ip.value_float > 0
            ORDER BY ip.record, ip.value_float DESC
        )
        UPDATE pms_board_service_line pbsl
        SET amount = COALESCE(
            (SELECT value_float
             FROM property_amounts pa
             WHERE pa.record = pbsl.id),
            1.0
        );
    """
    )

    _logger.info("Finished migrations")
