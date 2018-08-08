# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class WuBookChannelInfo(models.Model):
    _name = 'wubook.channel.info'

    wid = fields.Char("WuBook Channel ID", required=True)
    name = fields.Char("Channel Name", required=True)
    ical = fields.Boolean("ical", default=False)

    @api.multi
    def import_channels_info(self):
        return self.env['wubook'].import_channels_info()
