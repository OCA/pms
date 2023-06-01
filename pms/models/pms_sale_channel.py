from odoo import fields, models


class PmsSaleChannel(models.Model):
    _name = "pms.sale.channel"
    _description = "Sales Channel"
    _check_pms_properties_auto = True

    name = fields.Text(string="Sale Channel Name", help="The name of the sale channel")
    channel_type = fields.Selection(
        string="Sale Channel Type",
        help="Type of sale channel; it can be 'direct'(if there is"
        "no intermediary) or 'indirect'(if there are"
        "intermediaries between partner and property",
        selection=[("direct", "Direct"), ("indirect", "Indirect")],
    )
    is_on_line = fields.Boolean(
        string="On Line", help="Indicates if the sale channel is on-line"
    )
    product_pricelist_ids = fields.Many2many(
        string="Pricelists",
        help="Pricelists for a sale channel",
        comodel_name="product.pricelist",
        relation="pms_sale_channel_product_pricelist_rel",
        column1="pms_sale_channel_id",
        column2="product_pricelist_id",
        check_pms_properties=True,
        domain="[('is_pms_available', '=', True)]",
    )
    pms_property_ids = fields.Many2many(
        string="Properties",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        required=False,
        ondelete="restrict",
        comodel_name="pms.property",
        relation="pms_sale_channel_pms_property_rel",
        column1="pms_sale_channel_id",
        column2="pms_property_id",
        check_pms_properties=True,
    )
    icon = fields.Image(string="Logo", max_width=1024, max_height=1024, store=True)
