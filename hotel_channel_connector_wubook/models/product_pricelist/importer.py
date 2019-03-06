# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError
from odoo import api, _


class ProductPricelistImporter(Component):
    _inherit = 'channel.product.pricelist.importer'

    @api.model
    def import_pricing_plans(self):
        count = 0
        try:
            results = self.backend_adapter.get_pricing_plans()
        except ChannelConnectorError as err:
            self.create_issue(
                section='pricelist',
                internal_message=str(err),
                channel_message=err.data['message'])
        else:
            channel_product_listprice_obj = self.env['channel.product.pricelist']
            pricelist_mapper = self.component(usage='import.mapper',
                                              model_name='channel.product.pricelist')
            for plan in results:
                if 'vpid' in plan:
                    continue    # FIXME: Ignore Virtual Plans
                plan_record = pricelist_mapper.map_record(plan)
                plan_bind = channel_product_listprice_obj.search([
                    ('backend_id', '=', self.backend_record.id),
                    ('external_id', '=', str(plan['id'])),
                ], limit=1)
                if not plan_bind:
                    plan_bind = channel_product_listprice_obj.with_context({
                        'connector_no_export': True,
                    }).create(plan_record.values(for_create=True))
                else:
                    plan_bind.with_context({
                        'connector_no_export': True,
                    }).write(plan_record.values())
                self.binder.bind(str(plan['id']), plan_bind)
                count = count + 1
        return count


class ProductPricelistImportMapper(Component):
    _name = 'channel.product.pricelist.import.mapper'
    _inherit = 'channel.import.mapper'
    _apply_on = 'channel.product.pricelist'

    direct = [
        ('id', 'external_id'),
        ('name', 'name'),
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def pricelist_type(self, record):
        if record['daily'] == 1:
            return {'pricelist_type': 'daily'}
        else:
            # TODO: manage not daily plans in Hootel
            raise ChannelConnectorError(_("Can't map a pricing plan from wubook"), {
                'message': '',
            })

