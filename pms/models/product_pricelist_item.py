# Copyright 2017  Alexandre Díaz, Pablo Quesada, Darío Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"
    _check_pms_properties_auto = True

    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        comodel_name="pms.property",
        relation="product_pricelist_item_pms_property_rel",
        column1="product_pricelist_item_id",
        column2="pms_property_id",
        ondelete="restrict",
        check_pms_properties=True,
    )
    date_start_overnight = fields.Date(
        string="Start Date Overnight",
        help="Start date to apply daily pricelist items",
    )
    date_end_overnight = fields.Date(
        string="End Date Overnight",
        help="End date to apply daily pricelist items",
    )
    on_board_service = fields.Boolean(
        string="On Board Service",
        help="Those included in Board Services",
    )
    board_service_room_type_ids = fields.Many2many(
        string="Board Services",
        help="""Specify a Board services on Room Types.""",
        comodel_name="pms.board.service.room.type",
        relation="board_service_pricelist_item_rel",
        column1="pricelist_item_id",
        column2="board_service_id",
        ondelete="cascade",
        check_pms_properties=True,
    )
    pricelist_id = fields.Many2one(
        string="Pricelist",
        help="Pricelist in which this item is included",
        check_pms_properties=True,
    )
    product_id = fields.Many2one(
        string="Product",
        help="Product associated with the item",
        check_pms_properties=True,
    )
    product_tmpl_id = fields.Many2one(
        string="Product Template",
        help="Product template associated with the item",
        check_pms_properties=True,
    )
