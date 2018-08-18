# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

class ChannelHotelVirtualRoomRestriction(models.Model):
    _name = 'channel.hotel.virtual.room.restriction'
    _inherit = 'channel.binding'
    _inherits = {'hotel.virtual.room.restriction': 'odoo_id'}
    _description = 'Channel Hotel Virtual Room Restriction'

    odoo_id = fields.Many2one(comodel_names='hotel.virtual.room.restriction',
                              string='Hotel Virtual Room Restriction',
                              required=True,
                              ondelete='cascade')
    channel_plan_id = fields.Char("Channel Plan ID", readonly=True, old_name='wpid')
    is_daily_plan = fields.Boolean("Channel Daily Plan", default=True, old_name='wdaily_plan')

    @job(default_channel='root.channel')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def create_plan(self):
        self.ensure_one()
        if self._context.get('channel_action', True):
            with self.backend_id.work_on(self._name) as work:
                adapter = work.component(usage='backend.adapter')
                try:
                    channel_plan_id = adapter.create_rplan(self.name)
                    if channel_plan_id:
                        self.channel_plan_id = channel_plan_id
                except ValidationError as e:
                    self.create_issue('room', "Can't create restriction plan on channel", "sss")

    @job(default_channel='root.channel')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def update_plan_name(self):
        self.ensure_one()
        if self._context.get('channel_action', True):
            with self.backend_id.work_on(self._name) as work:
                adapter = work.component(usage='backend.adapter')
                try:
                    adapter.rename_rplan(
                        self.channel_plan_id,
                        self.name)
                except ValidationError as e:
                    self.create_issue('room', "Can't update restriction plan name on channel", "sss")

    @job(default_channel='root.channel')
    @related_action(action='related_action_unwrap_binding')
    @api.multi
    def delete_plan(self):
        self.ensure_one()
        if self._context.get('channel_action', True) and self.channel_room_id:
            with self.backend_id.work_on(self._name) as work:
                adapter = work.component(usage='backend.adapter')
                try:
                    adapter.delete_rplan(self.channel_plan_id)
                except ValidationError as e:
                    self.create_issue('room', "Can't delete restriction plan on channel", "sss")

    @job(default_channel='root.channel')
    @api.multi
    def import_restriction_plans(self):
        if self._context.get('channel_action', True):
            with self.backend_id.work_on(self._name) as work:
                importer = work.component(usage='channel.importer')
                return importer.import_restriction_plans()

class HotelVirtualRoomRestriction(models.Model):
    _inherit = 'hotel.virtual.room.restriction'

    channel_bind_ids = fields.One2many(
        comodel_name='channel.hotel.virtual.room.restriction',
        inverse_name='odoo_id',
        string='Hotel Channel Connector Bindings')

    @api.multi
    @api.depends('name')
    def name_get(self):
        vroom_restriction_obj = self.env['hotel.virtual.room.restriction']
        org_names = super(HotelVirtualRoomRestriction, self).name_get()
        names = []
        for name in org_names:
            restriction_id = vroom_restriction_obj.browse(name[0])
            if restriction_id.wpid:
                names.append((name[0], '%s (WuBook)' % name[1]))
            else:
                names.append((name[0], name[1]))
        return names

class ChannelBindingHotelVirtualRoomRestrictionListener(Component):
    _name = 'channel.binding.hotel.virtual.room.restriction.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['channel.hotel.virtual.room.restriction']

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
