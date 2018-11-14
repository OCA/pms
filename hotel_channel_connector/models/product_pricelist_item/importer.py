# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo.addons.hotel_channel_connector.components.backend_adapter import (
    DEFAULT_WUBOOK_DATE_FORMAT)
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import fields, api, _
_logger = logging.getLogger(__name__)


class ProductPricelistItemImporter(Component):
    _name = 'channel.product.pricelist.item.importer'
    _inherit = 'hotel.channel.importer'
    _apply_on = ['channel.product.pricelist.item']
    _usage = 'product.pricelist.item.importer'

    @api.model
    def _generate_pricelist_items(self, channel_plan_id, date_from, date_to, plan_prices):
        _logger.info("==[CHANNEL->ODOO]==== PRICELISTS [%d] (%s - %s) ==",
                     int(channel_plan_id), date_from, date_to)
        _logger.info(plan_prices)
        channel_hotel_room_type_obj = self.env['channel.hotel.room.type']
        pricelist_bind = self.env['channel.product.pricelist'].search([
            ('external_id', '=', channel_plan_id)
        ], limit=1)
        pricelist_item_mapper = self.component(
            usage='import.mapper',
            model_name='channel.product.pricelist.item')
        if pricelist_bind:
            channel_pricelist_item_obj = self.env['channel.product.pricelist.item']
            dfrom_dt = fields.Date.from_string(date_from)
            dto_dt = fields.Date.from_string(date_to)
            days_diff = (dto_dt-dfrom_dt).days + 1
            for i in range(0, days_diff):
                ndate_dt = dfrom_dt + timedelta(days=i)
                for k_rid, v_rid in plan_prices.items():
                    channel_room_type = channel_hotel_room_type_obj.search([
                        ('external_id', '=', k_rid)
                    ], limit=1)
                    if channel_room_type:
                        ndate_str = ndate_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                        item = {
                            'price': plan_prices[k_rid][i],
                            'channel_room_type': channel_room_type,
                            'pricelist_id': pricelist_bind.odoo_id.id,
                            'date': ndate_str,
                        }
                        map_record = pricelist_item_mapper.map_record(item)
                        pricelist_item = channel_pricelist_item_obj.search([
                            ('pricelist_id', '=', pricelist_bind.odoo_id.id),
                            ('date_start', '=', ndate_str),
                            ('date_end', '=', ndate_str),
                            ('compute_price', '=', 'fixed'),
                            ('applied_on', '=', '1_product'),
                            ('product_tmpl_id', '=',
                             channel_room_type.product_id.product_tmpl_id.id)
                        ], limit=1)
                        if pricelist_item:
                            pricelist_item.with_context({
                                'connector_no_export': True,
                            }).write(map_record.values())
                        else:
                            pricelist_item = channel_pricelist_item_obj.with_context({
                                'connector_no_export': True,
                            }).create(map_record.values(for_create=True))
                        pricelist_item.channel_pushed = True
        return True

    @api.model
    def import_all_pricelist_values(self, date_from, date_to, rooms=None):
        external_ids = self.env['channel.product.pricelist'].search([]).mapped('external_id')
        for external_id in external_ids:
            if external_id:
                self.import_pricelist_values(external_id, date_from, date_to, rooms=rooms)
        return True

    @api.model
    def import_pricelist_values(self, external_id, date_from, date_to, rooms=None):
        try:
            results = self.backend_adapter.fetch_plan_prices(
                external_id,
                date_from,
                date_to,
                rooms)
        except ChannelConnectorError as err:
            self.create_issue(
                section='pricelist',
                internal_message=str(err),
                channel_message=err.data['message'],
                channel_object_id=external_id,
                dfrom=date_from,
                dto=date_to)
        else:
            self._generate_pricelist_items(external_id, date_from, date_to, results)

class ProductPricelistItemImportMapper(Component):
    _name = 'channel.product.pricelist.item.import.mapper'
    _inherit = 'channel.import.mapper'
    _apply_on = 'channel.product.pricelist.item'

    direct = [
        ('price', 'fixed_price'),
        ('date', 'date_start'),
        ('date', 'date_end'),
    ]

    @only_create
    @mapping
    def compute_price(self, record):
        return {'compute_price': 'fixed'}

    @only_create
    @mapping
    def channel_pushed(self, record):
        return {'channel_pushed': True}

    @only_create
    @mapping
    def applied_on(self, record):
        return {'applied_on': '1_product'}

    @mapping
    def product_tmpl_id(self, record):
        return {'product_tmpl_id': record['channel_room_type'].product_id.product_tmpl_id.id}

    @mapping
    def pricelist_id(self, record):
        return {'pricelist_id': record['pricelist_id']}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}
