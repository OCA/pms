# Copyright 2017  Alexandre Díaz, Pablo Quesada, Darío Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ProductPricelist(models.Model):
    """Before creating a 'daily' pricelist, you need to consider the following:
    A pricelist marked as daily is used as a daily rate plan for room types and
    therefore is related only with one property.
    """

    _inherit = "product.pricelist"
    _check_pms_properties_auto = True

    # Fields declaration
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        required=False,
        comodel_name="pms.property",
        relation="product_pricelist_pms_property_rel",
        column1="product_pricelist_id",
        column2="pms_property_id",
        ondelete="restrict",
        check_pms_properties=True,
    )
    company_id = fields.Many2one(
        string="Company",
        help="Company to which the pricelist belongs",
        index=True,
    )
    cancelation_rule_id = fields.Many2one(
        string="Cancelation Policy",
        help="Cancelation Policy included in the room",
        comodel_name="pms.cancelation.rule",
        index=True,
        check_pms_properties=True,
    )
    pricelist_type = fields.Selection(
        string="Pricelist Type",
        help="Pricelist types, it can be Daily Plan",
        default="daily",
        selection=[("daily", "Daily Plan")],
    )
    pms_sale_channel_ids = fields.Many2many(
        string="Available Channels",
        help="Sale channel for which the pricelist is included",
        comodel_name="pms.sale.channel",
        check_pms_properties=True,
    )
    availability_plan_id = fields.Many2one(
        string="Availability Plan",
        help="Availability Plan for which the pricelist is included",
        comodel_name="pms.availability.plan",
        ondelete="restrict",
        index=True,
        check_pms_properties=True,
    )
    item_ids = fields.One2many(
        string="Items",
        help="Items for which the pricelist is made up",
        check_pms_properties=True,
    )
    is_pms_available = fields.Boolean(
        string="Available in PMS",
        help="If the pricelist is available in the PMS",
        default=False,
    )

    def _get_applicable_rules_domain(self, products, date, **kwargs):
        # Llamada al método original para obtener el dominio base
        domain = super(ProductPricelist, self)._get_applicable_rules_domain(
            products, date, **kwargs
        )

        # Si se pasa el parámetro "consumption_date", agregar condiciones adicionales al dominio
        consumption_date = kwargs.get("consumption_date")
        if consumption_date:
            domain.extend(
                [
                    "|",
                    ("date_start_consumption", "=", False),
                    ("date_start_consumption", "<=", consumption_date),
                    "|",
                    ("date_end_consumption", "=", False),
                    ("date_end_consumption", ">=", consumption_date),
                ]
            )

        return domain

    # V14.0
    # def _compute_price_rule_get_items(
    #     self, products_qty_partner, date, uom_id, prod_tmpl_ids, prod_ids, categ_ids
    # ):
    #     board_service = True if self._context.get("board_service") else False
    #     if (
    #         "property" in self._context
    #         and self._context["property"]
    #         and self._context.get("consumption_date")
    #     ):
    #         self.env.cr.execute(
    #             """
    #             SELECT item.id
    #             FROM   product_pricelist_item item
    #                    LEFT JOIN product_category categ
    #                         ON item.categ_id = categ.id
    #                    LEFT JOIN product_pricelist_pms_property_rel cab
    #                         ON item.pricelist_id = cab.product_pricelist_id
    #                    LEFT JOIN product_pricelist_item_pms_property_rel lin
    #                         ON item.id = lin.product_pricelist_item_id
    #             WHERE  (lin.pms_property_id = %s OR lin.pms_property_id IS NULL)
    #                AND (cab.pms_property_id = %s OR cab.pms_property_id IS NULL)
    #                AND (item.product_tmpl_id IS NULL
    #                     OR item.product_tmpl_id = ANY(%s))
    #                AND (item.product_id IS NULL OR item.product_id = ANY(%s))
    #                AND (item.categ_id IS NULL OR item.categ_id = ANY(%s))
    #                AND (item.pricelist_id = %s)
    #                AND (item.date_start IS NULL OR item.date_start <=%s)
    #                AND (item.date_end IS NULL OR item.date_end >=%s)
    #                AND (item.date_start_consumption IS NULL
    #                     OR item.date_start_consumption <=%s)
    #                AND (item.date_end_consumption IS NULL
    #                     OR item.date_end_consumption >=%s)
    #             GROUP  BY item.id
    #             ORDER  BY item.applied_on,
    #                       /* REVIEW: priotrity date sale / date consumption */
    #                       item.date_end - item.date_start ASC,
    #                       item.date_end_consumption - item.date_start_consumption ASC,
    #                       NULLIF((SELECT COUNT(1)
    #                        FROM   product_pricelist_item_pms_property_rel l
    #                        WHERE  item.id = l.product_pricelist_item_id)
    #                       + (SELECT COUNT(1)
    #                          FROM   product_pricelist_pms_property_rel c
    #                          WHERE  item.pricelist_id = c.product_pricelist_id),0)
    #                       NULLS LAST,
    #                       item.id DESC;
    #             """,
    #             (
    #                 self._context["property"],
    #                 self._context["property"],
    #                 prod_tmpl_ids,
    #                 prod_ids,
    #                 categ_ids,
    #                 self.id,
    #                 date,
    #                 date,
    #                 self._context["consumption_date"],
    #                 self._context["consumption_date"],
    #             ),
    #         )
    #         item_ids = [x[0] for x in self.env.cr.fetchall()]
    #         items = self.env["product.pricelist.item"].browse(item_ids)
    #         if board_service:
    #             items = items.filtered(
    #                 lambda x: x.board_service_room_type_id.id
    #                 == self._context.get("board_service")
    #             )
    #         else:
    #             items = items.filtered(lambda x: not x.board_service_room_type_id.id)
    #     else:
    #         items = super(ProductPricelist, self)._compute_price_rule_get_items(
    #             products_qty_partner, date, uom_id, prod_tmpl_ids, prod_ids, categ_ids
    #         )
    #     return items

    @api.constrains("is_pms_available", "availability_plan_id")
    def _check_is_pms_available(self):
        for record in self:
            if record.is_pms_available and not record.availability_plan_id:
                raise ValidationError(
                    _(
                        "If the pricelist is available in the PMS, "
                        "you must select an availability plan"
                    )
                )

    # Action methods
    # Constraints and onchanges
    # @api.constrains("pricelist_type", "pms_property_ids")
    # def _check_pricelist_type_property_ids(self):
    #     for record in self:
    #         if record.pricelist_type == "daily" and len(record.pms_property_ids) != 1:
    #             raise ValidationError(
    #                 _(
    #                     "A daily pricelist is used as a daily Rate Plan "
    #                     "for room types and therefore must be related with "
    #                     "one and only one property."
    #                 )
    #             )

    #         if record.pricelist_type == "daily" and len(record.pms_property_ids) == 1:
    #             pms_property_id = (
    #                 self.env["pms.property"].search(
    #                     [("default_pricelist_id", "=", record.id)]
    #                 )
    #                 or None
    #             )
    #             if pms_property_id and pms_property_id != record.pms_property_ids:
    #                 raise ValidationError(
    #                     _("Relationship mismatch.")
    #                     + " "
    #                     + _(
    #                         "This pricelist is used as default in a "
    #                         "different property."
    #                     )
    #                 )

    def open_massive_changes_wizard(self):

        if self.ensure_one():
            return {
                "view_type": "form",
                "view_mode": "form",
                "name": "Massive changes on Pricelist: " + self.name,
                "res_model": "pms.massive.changes.wizard",
                "target": "new",
                "type": "ir.actions.act_window",
                "context": {
                    "pricelist_id": self.id,
                },
            }
