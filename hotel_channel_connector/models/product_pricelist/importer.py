# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime, timedelta
from odoo.addons.component.core import Component
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo.addons.connector.components.mapper import mapping, only_create
from odoo.addons.hotel_channel_connector.components.backend_adapter import (
    DEFAULT_WUBOOK_DATE_FORMAT)
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import fields, api, _
_logger = logging.getLogger(__name__)


class ProductPricelistImporter(Component):
    _name = 'channel.product.pricelist.importer'
    _inherit = 'hotel.channel.importer'
    _apply_on = ['channel.product.pricelist']
    _usage = 'product.pricelist.importer'

    @api.model
    def import_pricing_plans(self):
        channel_product_listprice_obj = self.env['channel.product.pricelist']
        pricelist_mapper = self.component(usage='import.mapper',
                                          model_name='channel.product.pricelist')
        count = 0
        try:
            results = self.backend_adapter.get_pricing_plans()
            for plan in results:
                if 'vpid' in plan:
                    continue    # FIXME: Ignore Virtual Plans
                plan_record = pricelist_mapper.map_record(plan)
                plan_bind = channel_product_listprice_obj.search([
                    ('external_id', '=', str(plan['id']))
                ], limit=1)
                if not plan_bind:
                    channel_product_listprice_obj.with_context({
                        'wubook_action': False}).create(plan_record.values(for_create=True))
                else:
                    channel_product_listprice_obj.write(plan_record.values())
                count = count + 1
        except ChannelConnectorError as err:
            self.create_issue(
                section='pricelist',
                internal_message=_("Can't get pricing plans from wubook"),
                channel_message=err.data['message'])
            return 0
        return count


class ProductPricelistMapper(Component):
    _name = 'channel.product.pricelist.import.mapper'
    _inherit = 'channel.import.mapper'
    _apply_on = 'channel.product.pricelist'

    direct = [
        ('id', 'external_id'),
        ('name', 'name'),
        ('daily', 'is_daily_plan'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}
