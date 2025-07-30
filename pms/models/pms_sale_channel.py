from odoo import fields, models


class PmsSaleChannel(models.Model):
    _name = "pms.sale.channel"
    _description = "Sales Channel"
    _check_pms_properties_auto = True

    name = fields.Char(
        string="Sale Channel Name",
        help="The name of the sale channel",
    )
    channel_type = fields.Selection(
        selection=[("direct", "Direct"), ("indirect", "Indirect")],
        string="Sale Channel Type",
        help="Type of sale channel; it can be 'direct'(if there is"
        "no intermediary) or 'indirect'(if there are"
        "intermediaries between partner and property",
    )
    is_on_line = fields.Boolean(
        string="On Line",
        help="Indicates if the sale channel is on-line",
    )
    # product_pricelist_ids = fields.Many2many(
    #     comodel_name="product.pricelist",
    #     relation="pms_sale_channel_product_pricelist_rel",
    #     column1="pms_sale_channel_id",
    #     column2="product_pricelist_id",
    #     string="Pricelists",
    #     domain="[('is_pms_available', '=', True)]",
    #     help="Pricelists for a sale channel",
    #     check_pms_properties=True,
    # )
    pms_property_ids = fields.Many2many(
        comodel_name="pms.property",
        relation="pms_sale_channel_pms_property_rel",
        column1="pms_sale_channel_id",
        column2="pms_property_id",
        string="Properties",
        ondelete="restrict",
        help="Properties with access to the element;"
        " if not set, all properties can access",
        check_pms_properties=True,
    )
    icon = fields.Image(string="Logo", max_width=1024, max_height=1024)
    active = fields.Boolean(default=True)
