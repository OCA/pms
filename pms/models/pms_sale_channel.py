from odoo import fields, models


class PmsSaleChannel(models.Model):
    _name = "pms.sale.channel"
    _description = "Sales Channel"

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
    )
