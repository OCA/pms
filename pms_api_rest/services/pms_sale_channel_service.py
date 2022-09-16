from odoo import _
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PmsSaleChannelService(Component):
    _inherit = "base.rest.service"
    _name = "pms.sale.channel.service"
    _usage = "sale-channels"
    _collection = "pms.services"

    @restapi.method(
        [
            (
                [
                    "/",
                ],
                "GET",
            )
        ],
        input_param=Datamodel("pms.sale.channel.search.param"),
        output_param=Datamodel("pms.sale.channel.info", is_list=True),
        auth="jwt_api_pms",
    )
    def get_sale_channels(self, sale_channel_search_param):
        sale_channels_all_properties = self.env["pms.sale.channel"].search(
            [("pms_property_ids", "=", False)]
        )
        if sale_channel_search_param.pmsPropertyIds:
            sale_channels = set()
            for index, prop in enumerate(sale_channel_search_param.pmsPropertyIds):
                sale_channels_with_query_property = self.env["pms.sale.channel"].search(
                    [("pms_property_ids", "=", prop)]
                )
                if index == 0:
                    sale_channels = set(sale_channels_with_query_property.ids)
                else:
                    sale_channels = sale_channels.intersection(
                        set(sale_channels_with_query_property.ids)
                    )
            sale_channels_total = list(
                set(list(sale_channels) + sale_channels_all_properties.ids)
            )
        else:
            sale_channels_total = list(sale_channels_all_properties.ids)
        domain = [
            ("id", "in", sale_channels_total),
        ]

        result_sale_channels = []
        PmsSaleChannelInfo = self.env.datamodels["pms.sale.channel.info"]
        for sale_channel in self.env["pms.sale.channel"].search(
            domain,
        ):
            result_sale_channels.append(
                PmsSaleChannelInfo(
                    id=sale_channel.id,
                    name=sale_channel.name if sale_channel.name else None,
                    channelType=sale_channel.channel_type
                    if sale_channel.channel_type
                    else None,
                )
            )
        return result_sale_channels

    @restapi.method(
        [
            (
                [
                    "/<int:sale_channel_id>",
                ],
                "GET",
            )
        ],
        output_param=Datamodel("pms.sale.channel.info", is_list=False),
        auth="jwt_api_pms",
    )
    def get_sale_channel(self, sale_channel_id):
        sale_channel = self.env["pms.sale.channel"].search(
            [("id", "=", sale_channel_id)]
        )
        if sale_channel:
            PmsSaleChannelInfo = self.env.datamodels["pms.sale.channel.info"]
            return PmsSaleChannelInfo(
                id=sale_channel.id,
                name=sale_channel.name if sale_channel else None,
            )
        else:
            raise MissingError(_("Sale Channel not found"))
