# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
from odoo.addons.queue_job.job import job

class HotelChannelConnectorOTAInfo(models.Model):
    _name = 'hote.channel.connector.ota.info'

    ota_id = fields.Char("Channel OTA ID", required=True)
    name = fields.Char("OTA Name", required=True)
    ical = fields.Boolean("ical", default=False)

    @job(default_channel='root.channel')
    @api.multi
    def import_channels_info(self):
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            importer = work.component(usage='channel.importer')
            return importer.import_channels_info()
