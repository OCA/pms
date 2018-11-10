# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _


class HotelChannelConnectorIssue(models.Model):
    _inherit = 'hotel.channel.connector.issue'

    @api.model
    def create(self, vals):
        issue_id = super(HotelChannelConnectorIssue, self).create(vals)
        self.env['bus.hotel.calendar'].send_issue_notification(
            'warn',
            _("Oops! Issue Reported!!"),
            issue_id.id,
            issue_id.section,
            issue_id.message)
        return issue_id
