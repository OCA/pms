# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.hotel_channel_connector.components.core import ChannelConnectorError

class ChannelProductPricelistItem(models.Model):
    _name = 'channel.product.pricelist.item'
    _inherit = 'channel.binding'
    _inherits = {'product.pricelist.item': 'odoo_id'}
    _description = 'Channel Product Pricelist Item'

    odoo_id = fields.Many2one(comodel_name='product.pricelist.item',
                              string='Hotel Product Pricelist Item',
                              required=True,
                              ondelete='cascade')
    channel_pushed = fields.Boolean("Channel Pushed", readonly=True, default=False,
                                    old_name='wpushed')

    @job(default_channel='root.channel')
    @api.model
    def import_pricelist_values(self, backend):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='product.pricelist.item.importer')
            try:
                if not backend.pricelist_id:
                    return importer.import_all_pricelist_values(
                        backend.pricelist_from,
                        backend.pricelist_to)
                return importer.import_pricelist_values(
                    backend.pricelist_id.external_id,
                    backend.pricelist_from,
                    backend.pricelist_to)
            except ChannelConnectorError as err:
                self.create_issue(
                    backend=backend.id,
                    section='pricelist',
                    internal_message=str(err),
                    channel_message=err.data['message'],
                    channel_object_id=backend.pricelist_id.external_id,
                    dfrom=backend.pricelist_from,
                    dto=backend.pricelist_to)
                return False

    @job(default_channel='root.channel')
    @api.model
    def push_pricelist(self, backend):
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='product.pricelist.item.exporter')
            try:
                return exporter.push_pricelist()
            except ChannelConnectorError as err:
                self.create_issue(
                    backend=backend.id,
                    section='pricelist',
                    internal_message=str(err),
                    channel_message=err.data['message'])

class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    channel_bind_ids = fields.One2many(
        comodel_name='channel.product.pricelist.item',
        inverse_name='odoo_id',
        string='Hotel Channel Connector Bindings')

class ProducrPricelistItemAdapter(Component):
    _name = 'channel.product.pricelist.item.adapter'
    _inherit = 'wubook.adapter'
    _apply_on = 'channel.product.pricelist.item'

    def fetch_plan_prices(self, external_id, date_from, date_to, rooms):
        return super(ProducrPricelistItemAdapter, self).fetch_plan_prices(
            external_id,
            date_from,
            date_to,
            rooms)

class BindingProductPricelistItemListener(Component):
    _name = 'binding.product.pricelist.item.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.pricelist.item']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        fields_to_check = ('date_start', 'date_end', 'fixed_price', 'product_tmpl_id')
        fields_checked = [elm for elm in fields_to_check if elm in fields]
        if any(fields_checked):
            record.channel_bind_ids.write({'channel_pushed': False})

class ChannelBindingProductPricelistItemListener(Component):
    _name = 'channel.binding.product.pricelist.item.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.product.pricelist.item']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        fields_to_check = ('date_start', 'date_end', 'fixed_price', 'product_tmpl_id')
        fields_checked = [elm for elm in fields_to_check if elm in fields]
        if any(fields_checked):
            record.channel_pushed = False
