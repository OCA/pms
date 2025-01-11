from odoo import _
from odoo.exceptions import MissingError

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component

from ..pms_api_rest_utils import pms_api_check_access, url_image_pms_api_rest


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
        sale_channels_all_properties = (
            self.env["pms.sale.channel"]
            .sudo()
            .search([("pms_property_ids", "=", False)])
        )
        if sale_channel_search_param.pmsPropertyIds:
            sale_channels = set()
            for index, prop in enumerate(sale_channel_search_param.pmsPropertyIds):
                sale_channels_with_query_property = (
                    self.env["pms.sale.channel"]
                    .sudo()
                    .search([("pms_property_ids", "=", prop)])
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
        if sale_channel_search_param.isOnLine:
            domain.append(("is_on_line", "=", sale_channel_search_param.isOnLine))

        result_sale_channels = []
        PmsSaleChannelInfo = self.env.datamodels["pms.sale.channel.info"]
        sale_channels = self.env["pms.sale.channel"].sudo().search(domain)
        pms_api_check_access(user=self.env.user, records=sale_channels)
        for sale_channel in sale_channels:
            result_sale_channels.append(
                PmsSaleChannelInfo(
                    id=sale_channel.id,
                    name=sale_channel.name if sale_channel.name else None,
                    channelType=sale_channel.channel_type
                    if sale_channel.channel_type
                    else None,
                    iconUrl=url_image_pms_api_rest(
                        "pms.sale.channel", sale_channel.id, "icon"
                    ),
                    isOnLine=sale_channel.is_on_line,
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
        sale_channel = self.env["pms.sale.channel"].sudo().browse(sale_channel_id)
        if not sale_channel.exists():
            raise MissingError(_("Sale Channel not found"))
        pms_api_check_access(user=self.env.user, records=sale_channel)
        PmsSaleChannelInfo = self.env.datamodels["pms.sale.channel.info"]
        return PmsSaleChannelInfo(
            id=sale_channel.id,
            name=sale_channel.name if sale_channel else None,
        )
