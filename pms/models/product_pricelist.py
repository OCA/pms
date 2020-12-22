# Copyright 2017  Alexandre Díaz, Pablo Quesada, Darío Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ProductPricelist(models.Model):
    """Before creating a 'daily' pricelist, you need to consider the following:
    A pricelist marked as daily is used as a daily rate plan for room types and
    therefore is related only with one property.
    """

    _inherit = "product.pricelist"

    # Fields declaration
    pms_property_ids = fields.Many2many(
        "pms.property", string="Properties", required=False, ondelete="restrict"
    )
    cancelation_rule_id = fields.Many2one(
        "pms.cancelation.rule", string="Cancelation Policy"
    )
    pricelist_type = fields.Selection(
        [("daily", "Daily Plan")], string="Pricelist Type", default="daily"
    )

    availability_plan_id = fields.Many2one(
        comodel_name="pms.room.type.availability.plan",
        string="Availability Plan",
        ondelete="restrict",
    )

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

    def _compute_price_rule_get_items(
        self, products_qty_partner, date, uom_id, prod_tmpl_ids, prod_ids, categ_ids
    ):
        items = super(ProductPricelist, self)._compute_price_rule_get_items(
            products_qty_partner, date, uom_id, prod_tmpl_ids, prod_ids, categ_ids
        )
        # Discard the rules with defined properties other than the context,
        # and we reorder the rules to return the most concrete property rule first
        if "property" in self._context:
            items_filtered = items.filtered(
                lambda i: not i.pms_property_ids
                or self._context["property"] in i.pms_property_ids.ids
            )
            reverse_id = items_filtered.sorted(id, reverse=True)
            return items_filtered.sorted(
                key=lambda s: (
                    s.applied_on,
                    True if (not s.date_end or not s.date_start) else False,
                    True
                    if (not s.date_end or not s.date_start)
                    else (s.date_end - s.date_start).days,
                    ((not s.pms_property_ids, s), len(s.pms_property_ids)),
                    reverse_id,
                )
            )
        return items

    # Action methods
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
