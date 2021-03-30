# Copyright 2017  Alexandre Díaz, Pablo Quesada, Darío Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    pms_property_ids = fields.Many2many(
        "pms.property", string="Properties", required=False, ondelete="restrict"
    )
    date_start_overnight = fields.Date(
        string="Start Date Overnight",
        help="Start date to apply daily pricelist items",
    )
    date_end_overnight = fields.Date(
        string="End Date Overnight",
        help="End date to apply daily pricelist items",
    )
    on_board_service = fields.Boolean("Those included in Board Services")
    board_service_room_type_ids = fields.Many2many(
        "pms.board.service.room.type",
        "board_service_pricelist_item_rel",
        "pricelist_item_id",
        "board_service_id",
        string="Board Services on Room Types",
        ondelete="cascade",  # check_company=True,
        help="""Specify a Board services on Room Types.""",
        # domain="[('pms_property_ids', 'in', [allowed_property_ids, False])]",
    )

    allowed_property_ids = fields.Many2many(
        "pms.property",
        "allowed_pricelist_move_rel",
        "pricelist_item_id",
        "property_id",
        string="Allowed Properties",
        store=True,
        readonly=True,
        compute="_compute_allowed_property_ids",
    )

    @api.depends("product_id.pms_property_ids", "pricelist_id.pms_property_ids")
    def _compute_allowed_property_ids(self):
        for record in self:
            properties = []
            if record.applied_on == "0_product_variant":
                product = record.product_id
            elif record.applied_on == "1_product":
                product = record.product_tmpl_id
            else:
                product = False
            if not record.pricelist_id.pms_property_ids or not product:
                record.allowed_property_ids = False
            else:
                if record.pricelist_id.pms_property_ids:
                    if product.pms_property_ids:
                        properties = list(
                            set(record.pricelist_id.pms_property_ids.ids)
                            & set(product.pms_property_ids.ids)
                        )
                        record.allowed_property_ids = self.env["pms.property"].search(
                            [("id", "in", properties)]
                        )
                    else:
                        record.allowed_property_ids = product.pms_property_ids
                else:
                    record.allowed_property_ids = product.pms_property_ids
            # else:
            #   record.allowed_property_ids = False

    @api.constrains(
        "allowed_property_ids",
        "pms_property_ids",
    )
    def _check_property_integrity(self):
        for rec in self:
            if rec.pms_property_ids and rec.allowed_property_ids:
                for p in rec.pms_property_ids:
                    if p.id not in rec.allowed_property_ids.ids:
                        raise ValidationError(_("Property not allowed"))
