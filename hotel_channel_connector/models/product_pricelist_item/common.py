# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.job import job
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if


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
    def import_pricelist_values(self, backend, dfrom, dto, external_id):
        with backend.work_on(self._name) as work:
            importer = work.component(usage='product.pricelist.item.importer')
            if not backend.pricelist_id:
                return importer.import_all_pricelist_values(
                    dfrom,
                    dto)
            return importer.import_pricelist_values(
                external_id,
                dfrom,
                dto)

    @job(default_channel='root.channel')
    @api.model
    def push_pricelist(self, backend):
        with backend.work_on(self._name) as work:
            exporter = work.component(usage='product.pricelist.item.exporter')
            return exporter.push_pricelist()

class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    channel_bind_ids = fields.One2many(
        comodel_name='channel.product.pricelist.item',
        inverse_name='odoo_id',
        string='Hotel Channel Connector Bindings')

    @api.constrains('fixed_price')
    def _check_fixed_price(self):
        for record in self:
            channel_room_type = self.env['channel.hotel.room.type'].search(
                [('product_tmpl_id', '=', record.product_tmpl_id.id)])
            if channel_room_type and (record.fixed_price < channel_room_type.min_price or \
                    record.fixed_price > channel_room_type.max_price):
                msg = _("The room type '%s' limits the price between '%s' and '%s'.") \
                      % (record.name, channel_room_type.min_price, channel_room_type.max_price)
                raise ValidationError(msg)

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

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        if not any(record.channel_bind_ids):
            channel_product_pricelist_item_obj = self.env[
                'channel.product.pricelist.item']
            for pricelist_bind in record.pricelist_id.channel_bind_ids:
                pricelist_item_bind = channel_product_pricelist_item_obj.search([
                    ('odoo_id', '=', record.id),
                    ('backend_id', '=', pricelist_bind.backend_id.id),
                ])
                if not pricelist_item_bind:
                    channel_product_pricelist_item_obj.create({
                        'odoo_id': record.id,
                        'channel_pushed': False,
                        'backend_id': pricelist_bind.backend_id.id,
                    })

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
