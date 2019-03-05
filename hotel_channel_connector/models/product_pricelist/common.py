# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.addons.queue_job.job import job
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

    is_virtual_plan = fields.Boolean("Is a Virtual Pricing Plan", compute='_compute_virtual_plan',
                                     help="A virtual plan is based on another Pricelist "
                                          "with a fixed or percentage variation.")

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
                'default_is_daily_plan': self.is_daily_plan,
                'default_is_virtual_plan': self.is_virtual_plan,
            }
        return action

    @api.multi
    def disconnect_channel_bind_ids(self):
        channel_bind_ids = self.mapped('channel_bind_ids')
        msg = _("This function is not yet implemented.")
        msg += _(" The pricelist [%s] should be delete from the channel manager.") % channel_bind_ids.get_external_id
        raise UserError(msg)


class BindingProductPricelistListener(Component):
    _name = 'binding.product.pricelist.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.pricelist']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if 'name' in fields:
            for binding in record.channel_bind_ids:
                binding.update_plan_name()


class ChannelBindingProductPricelistListener(Component):
    _name = 'channel.binding.product.pricelist.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.product.pricelist']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        if record.is_virtual_plan:
            record.create_vplan()
        else:
            record.create_plan()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        record.delete_plan()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if 'name' in fields:
            record.update_plan_name()
