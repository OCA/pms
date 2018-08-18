# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

class ChannelHotelVirtualRoomAvailability(models.Model):
    _name = 'channel.hotel.virtual.room.availability'
    _inherit = 'channel.binding'
    _inherits = {'hotel.virtual.room.availability': 'odoo_id'}
    _description = 'Channel Product Pricelist'

    @api.model
    def _default_channel_max_avail(self):
        if self.virtual_room_id:
            return self.virtual_room_id.max_real_rooms
        return -1

    odoo_id = fields.Many2one(comodel_names='product.pricelist',
                              string='Pricelist',
                              required=True,
                              ondelete='cascade')
    channel_max_avail = fields.Integer("Max. Channel Avail",
                                       default=_default_channel_max_avail,
                                       old_name='wmax_avail')
    channel_pushed = fields.Boolean("Channel Pushed", readonly=True, default=False,
                                    old_name='wpushed')

    @job(default_channel='root.channel')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def create_plan(self):
        self.ensure_one()
        if self._context.get('channel_action', True):
            with self.backend_id.work_on(self._name) as work:
                adapter = work.component(usage='backend.adapter')
                try:
                    channel_plan_id = adapter.create_plan(self.name,
                                                          self.is_daily_plan and 1 or 0)
                    if channel_plan_id:
                        self.channel_plan_id = channel_plan_id
                except ValidationError as e:
                    self.create_issue('room', "Can't create plan on channel", "sss")

    @job(default_channel='root.channel')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def update_plan_name(self):
        self.ensure_one()
        if self._context.get('channel_action', True):
            with self.backend_id.work_on(self._name) as work:
                adapter = work.component(usage='backend.adapter')
                try:
                    adapter.update_plan_name(
                        self.channel_plan_id,
                        self.name)
                except ValidationError as e:
                    self.create_issue('room', "Can't update plan name on channel", "sss")

    @job(default_channel='root.channel')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def delete_plan(self):
        self.ensure_one()
        if self._context.get('channel_action', True) and self.channel_room_id:
            with self.backend_id.work_on(self._name) as work:
                adapter = work.component(usage='backend.adapter')
                try:
                    adapter.delete_plan(self.channel_plan_id)
                except ValidationError as e:
                    self.create_issue('room', "Can't delete plan on channel", "sss")

    @job(default_channel='root.channel')
    @api.multi
    def import_price_plans(self):
        if self._context.get('channel_action', True):
            with self.backend_id.work_on(self._name) as work:
                importer = work.component(usage='channel.importer')
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
            if priclist_id.wpid:
                names.append((name[0], '%s (WuBook)' % name[1]))
            else:
                names.append((name[0], name[1]))
        return names

class ChannelBindingProductPricelistListener(Component):
    _name = 'channel.binding.product.pricelist.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.product.pricelist']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        record.with_delay(priority=20).create_plan()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record, fields=None):
        record.with_delay(priority=20).delete_plan()

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if 'name' in fields:
            record.with_delay(priority=20).update_plan_name()
