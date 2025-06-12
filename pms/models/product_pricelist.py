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
        domain = super()._get_applicable_rules_domain(products, date, **kwargs)
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
        if "pms_property_id" in kwargs:
            domain.extend(
                [
                    "|",
                    ("pms_property_ids", "=", False),
                    ("pms_property_ids", "in", [kwargs["pms_property_id"]]),
                ]
            )
        return domain

    def _compute_price_rule(self, products, qty, uom=None, date=False, **kwargs):
        """Inherit the method to add the consumption date logic
        if consuption_date is passed as a parameter in kwargs
        fork the method to get the items to apply the rules
        """
        consumption_date = kwargs.get("consumption_date")
        if not consumption_date:
            return super()._compute_price_rule(
                products, qty, uom=uom, date=date, **kwargs
            )
        self.ensure_one()
        if not products:
            return {}

        if not date:
            # Used to fetch pricelist rules and currency rates
            date = fields.Datetime.now()

        pms_property_id = kwargs.get("pms_property_id")
        if not pms_property_id:
            raise ValidationError(_("Property is required in pms context"))

        # Fetch all rules potentially matching specified products/templates/categories
        # and date
        rules = self._get_applicable_rules(products, date, **kwargs)

        results = {}
        for product in products:
            suitable_rule = self.env["product.pricelist.item"]

            product_uom = product.uom_id
            target_uom = (
                uom or product_uom
            )  # If no uom is specified, fall back on the product uom

            # Compute quantity in product uom because pricelist rules are specified
            # w.r.t product default UoM (min_quantity, price_surchage, ...)
            if target_uom != product_uom:
                qty_in_product_uom = target_uom._compute_quantity(
                    qty, product_uom, raise_if_failure=False
                )
            else:
                qty_in_product_uom = qty

            for rule in rules:
                if rule._is_applicable_for(product, qty_in_product_uom):
                    suitable_rule = rule
                    break

            kwargs["pricelist"] = self
            price = suitable_rule._compute_consumption_price(
                product=product,
                quantity=qty,
                uom=target_uom,
                date=date,
                currency=self.currency_id,
                **kwargs,
            )
            results[product.id] = (price, suitable_rule.id)

        return results

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
