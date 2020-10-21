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
