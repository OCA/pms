# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if


class ChannelProductPricelist(models.Model):
    _name = 'channel.product.pricelist'
    _inherit = 'channel.binding'
    _inherits = {'product.pricelist': 'odoo_id'}
    _description = 'Channel Product Pricelist'

    odoo_id = fields.Many2one(comodel_name='product.pricelist',
                              string='Pricelist',
                              required=True,
                              ondelete='cascade')
    is_daily_plan = fields.Boolean("Channel Daily Plan", default=True, old_name='wdaily_plan')

    @job(default_channel='root.channel')
    @api.multi
    def create_plan(self):
        self.ensure_one()
        if not self.external_id:
            with self.backend_id.work_on(self._name) as work:
                exporter = work.component(usage='product.pricelist.exporter')
                exporter.create_plan(self)

    @job(default_channel='root.channel')
    @api.multi
    def update_plan_name(self):
        self.ensure_one()
        if self.external_id:
            with self.backend_id.work_on(self._name) as work:
                exporter = work.component(usage='product.pricelist.exporter')
                exporter.rename_plan(self)

    @job(default_channel='root.channel')
    @api.multi
    def delete_plan(self):
        self.ensure_one()
        if self.external_id:
            with self.backend_id.work_on(self._name) as work:
                deleter = work.component(usage='product.pricelist.deleter')
                deleter.delete_plan(self)

    @job(default_channel='root.channel')
    @api.model
    def import_price_plans(self, backend):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='product.pricelist.importer')
            return importer.import_pricing_plans()

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    channel_bind_ids = fields.One2many(
        comodel_name='channel.product.pricelist',
        inverse_name='odoo_id',
        string='Hotel Channel Connector Bindings')

    @api.multi
    @api.depends('name')
    def name_get(self):
        pricelist_obj = self.env['product.pricelist']
        org_names = super(ProductPricelist, self).name_get()
        names = []
        for name in org_names:
            priclist_id = pricelist_obj.browse(name[0])
            if any(priclist_id.channel_bind_ids) and \
                    priclist_id.channel_bind_ids[0].external_id:
                names.append((name[0], '%s (%s Backend)' % (
                    name[1],
                    priclist_id.channel_bind_ids[0].backend_id.name)))
            else:
                names.append((name[0], name[1]))
        return names

class ProductPricelistAdapter(Component):
    _name = 'channel.product.pricelist.adapter'
    _inherit = 'wubook.adapter'
    _apply_on = 'channel.product.pricelist'

    def get_pricing_plans(self):
        return super(ProductPricelistAdapter, self).get_pricing_plans()

    def create_plan(self, name):
        return super(ProductPricelistAdapter, self).create_plan(name)

    def delete_plan(self, external_id):
        return super(ProductPricelistAdapter, self).delete_plan(external_id)

    def rename_plan(self, external_id, new_name):
        return super(ProductPricelistAdapter, self).rename_plan(external_id, new_name)

class BindingProductPricelistListener(Component):
    _name = 'binding.product.pricelist.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.pricelist']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if any(record.channel_bind_ids) and 'name' in fields:
            record.channel_bind_ids[0].update_plan_name()

class ChannelBindingProductPricelistListener(Component):
    _name = 'channel.binding.product.pricelist.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.product.pricelist']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.create_plan()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        record.delete_plan()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if 'name' in fields:
            record.update_plan_name()
