def migrate(cr, version):
    cr.execute(
        """
               DO $$
DECLARE
    table_name TEXT;
BEGIN
    FOR table_name IN
        SELECT relation_table
        FROM ir_model_fields
        WHERE name IN (
        'allowed_board_service_product_ids', 'allowed_board_service_room_type_ids')
          AND model = 'product.pricelist.item'
          AND relation_table IS NOT NULL
    LOOP
        EXECUTE format('DROP TABLE IF EXISTS %I', table_name);
        RAISE NOTICE 'Tabla eliminada: %', table_name;
    END LOOP;
END $$;
               """
    )
