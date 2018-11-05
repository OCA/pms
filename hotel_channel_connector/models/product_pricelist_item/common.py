# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields
from odoo.exceptions import ValidationError
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if

class ChannelProductPricelistItem(models.Model):
    _name = 'channel.product.pricelist.item'
    _inherit = 'channel.binding'
    _inherits = {'product.pricelist.item': 'odoo_id'}
    _description = 'Channel Product Pricelist Item'

    odoo_id = fields.Many2one(comodel_name='product.pricelist.item',
                              string='Pricelist Item',
                              required=True,
                              ondelete='cascade')

    channel_pushed = fields.Boolean("Channel Pushed", readonly=True, default=False,
                                    old_name='wpushed')

class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    channel_bind_ids = fields.One2many(
        comodel_name='channel.product.pricelist.item',
        inverse_name='odoo_id',
        string='Hotel Channel Connector Bindings')
