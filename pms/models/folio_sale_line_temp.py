from odoo import _, api, fields, models


class FolioSaleLineTemp(models.Model):
    _name = "folio.sale.line.temp"
    _description = "Folio Sale Line Temp"
    _auto = False

    folio_id = fields.Many2one(
        string="Folio Reference",
        help="Folio to which folio sale line belongs",
        comodel_name="pms.folio",
    )
    reservation_id = fields.Many2one(
        string="Reservation Reference",
        help="Reservation to which folio sale line belongs",
        comodel_name="pms.reservation",
    )
    service_id = fields.Many2one(
        string="Service Reference",
        help="Sevice included in folio sale line",
        comodel_name="pms.service",
    )
    pms_property_id = fields.Many2one(
        string="Property",
        help="Property with access to the element;",
        comodel_name="pms.property",
    )
    is_board_service = fields.Boolean(
        string="Board Service",
        help="Indicates if the service included in "
        "folio sale line is part of a board service",
    )
    display_name = fields.Text(
        string="Description",
        help="Description of folio sale line",
    )
    price_unit = fields.Float(
        string="Unit Price",
        help="Unit Price of folio sale line",
        digits="Product Price",
    )
    discount = fields.Float(
        string="Discount (%)",
        help="Discount of total price in folio sale line",
        readonly=False,
        digits="Discount",
        # compute="_compute_discount",
    )
    product_id = fields.Many2one(
        string="Product",
        help="Product associated with folio sale line, "
        "can be product associated with service "
        "or product associated with"
        "reservation's room type, in other case it's false",
        comodel_name="product.product",
        domain="[('sale_ok', '=', True),\
            ('is_pms_available', '=', True),\
            '|', ('company_id', '=', False), \
            ('company_id', '=', company_id)]",
        ondelete="restrict",
        check_company=True,
        change_default=True,
    )
    product_uom_qty = fields.Float(
        string="Quantity",
        help="",
        readonly=False,
        digits="Product Unit of Measure",
    )
    company_id = fields.Many2one(
        string="Company",
        help="The company in the folio sale line",
        readonly=True,
        index=True,
    )
    date_order = fields.Date(
        string="Date",
        help="Field to order by service",
    )
    default_invoice_to = fields.Many2one(
        string="Invoice to",
        help="""Indicates the contact to which this line will be
        billed by default, if it is not established,
        a guest or the generic contact will be used instead""",
        comodel_name="res.partner",
    )

    @property
    def _table_query(self):
        sql = """
            SELECT 	row_number() OVER () id, display_name, folio_id, reservation_id, service_id, product_id, price_unit,
                    discount, cancel_discount, product_uom_qty, default_invoice_to, is_board_service, company_id,
                    pms_property_id, date_order
            FROM (
                SELECT 	display_name, folio_id, reservation_id, service_id, product_id, price_unit,
                        discount, cancel_discount, product_uom_qty, default_invoice_to, is_board_service, company_id,
                        pms_property_id, date_order
                FROM (
                    SELECT  NULL display_name, r.folio_id, l.reservation_id, NULL service_id, rt.product_id,
                            l.price price_unit, l.discount, l.cancel_discount, SUM(1) product_uom_qty, l.default_invoice_to,
                            NULL is_board_service, r.company_id, r.pms_property_id, r.create_date date_order
                    FROM pms_reservation_line l
                    INNER JOIN pms_reservation r ON r.id = l.reservation_id
                    INNER JOIN pms_room_type rt ON rt.id = r.room_type_id
                    GROUP BY    r.folio_id, l.reservation_id, rt.product_id, l.price, l.discount, l.cancel_discount,
                                l.default_invoice_to, r.company_id, r.pms_property_id, r.create_date
                    UNION
                    SELECT  NULL, s.folio_id, s.reservation_id, s.id, s.product_id, sl.price_unit, sl.discount,
                            sl.cancel_discount, SUM(sl.day_qty), sl.default_invoice_to, sl.is_board_service, s.company_id,
                            s.pms_property_id, s.create_date
                    FROM pms_service s
                    INNER JOIN pms_service_line sl ON s.id = sl.service_id
                    WHERE s.reservation_id IS NOT NULL
                    GROUP BY    s.folio_id, s.id, s.product_id, sl.price_unit, sl.discount, sl.cancel_discount,
                                sl.default_invoice_to, sl.is_board_service, s.pms_property_id
                    UNION
                    SELECT  NULL, s.folio_id, s.reservation_id, s.id, s.product_id, sl.price_unit, sl.discount,
                            sl.cancel_discount, SUM(sl.day_qty), sl.default_invoice_to, sl.is_board_service, s.company_id,
                            s.pms_property_id, s.create_date
                    FROM pms_service s
                    INNER JOIN pms_service_line sl ON s.id = sl.service_id
                    WHERE s.reservation_id IS NULL
                    GROUP BY    s.folio_id, s.id, s.product_id, sl.price_unit, sl.discount, sl.cancel_discount,
                                sl.default_invoice_to, sl.is_board_service, s.pms_property_id
                    UNION
                    SELECT 	'Other', f.id, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
                    FROM pms_folio f
                    WHERE EXISTS (	SELECT 1
                                    FROM pms_service
                                    WHERE folio_id = f.id AND reservation_id IS NULL
                                    GROUP BY folio_id
                    )
                ) reservation_and_service_sale_lines
                UNION
                SELECT 	f.name || '/' || r.folio_sequence display_name, f.id, r.id, NULL, NULL, NULL, NULL, NULL, NULL,
                        NULL, NULL, NULL, NULL, NULL
                FROM pms_reservation r
                INNER JOIN pms_folio f ON f.id = r.folio_id
                ORDER BY folio_id, reservation_id NULLS LAST, service_id NULLS FIRST, price_unit NULLS FIRST
            ) reservation_lines_and_titles
        """
        return sql
