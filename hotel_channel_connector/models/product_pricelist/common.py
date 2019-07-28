# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
import logging
_logger = logging.getLogger(__name__)


class ChannelProductPricelist(models.Model):
    _name = 'channel.product.pricelist'
    _inherit = 'channel.binding'
    _inherits = {'product.pricelist': 'odoo_id'}
    _description = 'Channel Product Pricelist'

    odoo_id = fields.Many2one(comodel_name='product.pricelist',
                              string='Pricelist',
                              required=True,
                              ondelete='cascade')

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
    def create_vplan(self):
        self.ensure_one()
        if not self.external_id:
            with self.backend_id.work_on(self._name) as work:
                exporter = work.component(usage='product.pricelist.exporter')
                exporter.create_vplan(self)

    @job(default_channel='root.channel')
    @api.multi
    def modify_vplan(self):
        self.ensure_one()
        if self.external_id:
            with self.backend_id.work_on(self._name) as work:
                exporter = work.component(usage='product.pricelist.exporter')
                exporter.modify_vplan(self)

    @job(default_channel='root.channel')
    @api.multi
    def update_plan_name(self):
        self.ensure_one()
        if self.external_id:
            with self.backend_id.work_on(self._name) as work:
                exporter = work.component(usage='product.pricelist.exporter')
                exporter.update_plan_name(self)

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

    pricelist_type = fields.Selection(selection_add=[
        ('virtual', 'Virtual Plan'),
    ])

    @api.depends('item_ids')
    def _compute_virtual_plan(self):
        for record in self:
            record.is_virtual_plan = True
            if any(item.applied_on != '3_global'
                   or (item.date_start or item.date_end)
                   or item.compute_price != 'formula'
                   or item.base != 'pricelist'
                   or not item.base_pricelist_id.is_daily_plan
                   or (item.price_discount != 0 and item.price_surcharge != 0)
                   or item.min_quantity != 0
                   or item.price_round != 0
                   or item.price_min_margin != 0
                   or item.price_max_margin != 0
                   for item in record.item_ids):
                record.is_virtual_plan = False

    @api.multi
    @api.depends('name')
    def name_get(self):
        pricelist_obj = self.env['product.pricelist']
        org_names = super(ProductPricelist, self).name_get()
        names = []
        for name in org_names:
            pricelist_id = pricelist_obj.browse(name[0])
            new_name = name[1]
            if any(pricelist_id.channel_bind_ids):
                for pricelist_bind in pricelist_id.channel_bind_ids:
                    if pricelist_bind.external_id:
                        new_name += ' (%s Backend)' % pricelist_bind.backend_id.name
                names.append((name[0], new_name))
            else:
                names.append((name[0], name[1]))
        return names

    @api.multi
    def open_channel_bind_ids(self):
        channel_bind_ids = self.mapped('channel_bind_ids')
        action = self.env.ref('hotel_channel_connector.channel_product_pricelist_action').read()[0]
        action['views'] = [(self.env.ref('hotel_channel_connector.channel_product_pricelist_view_form').id, 'form')]
        action['target'] = 'new'
        if len(channel_bind_ids) == 1:
            action['res_id'] = channel_bind_ids.ids[0]
        elif len(channel_bind_ids) > 1:
            # WARNING: more than one binding is currently not expected
            action['domain'] = [('id', 'in', channel_bind_ids.ids)]
        else:
            action['context'] = {
                'default_odoo_id': self.id,
                'default_name': self.name,
                'default_pricelist_plan': self.pricelist_type,
            }
        return action

    @api.multi
    def disconnect_channel_bind_ids(self):
        # TODO: multichannel rooms is not implemented
        self.channel_bind_ids.with_context({'connector_no_export': True}).unlink()

    @api.multi
    def write(self, vals):
        if 'active' in vals and vals.get('active') is False:
            self.channel_bind_ids.unlink()
        return super().write(vals)


class BindingProductPricelistListener(Component):
    _name = 'binding.product.pricelist.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.pricelist']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if 'name' in fields:
            for binding in record.channel_bind_ids:
                binding.update_plan_name()
        if 'item_ids' in fields and record.pricelist_type == 'virtual':
            for binding in record.channel_bind_ids:
                binding.modify_vplan()


class ChannelBindingProductPricelistListener(Component):
    _name = 'channel.binding.product.pricelist.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.product.pricelist']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        if record.pricelist_type == 'daily':
            record.create_plan()
        elif record.pricelist_type == 'virtual':
            record.create_vplan()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        record.delete_plan()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if 'name' in fields:
            record.update_plan_name()
