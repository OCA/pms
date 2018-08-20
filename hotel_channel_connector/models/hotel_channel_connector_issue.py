# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class HotelChannelConnectorIssue(models.Model):
    _name = 'hotel.channel.connector.issue'
    _old_name = 'wubook.issue'

    section = fields.Selection([
        ('channel', 'Channel'),
        ('reservation', 'Reservation'),
        ('rplan', 'Restriction Plan'),
        ('plan', 'Price Plan'),
        ('room', 'Room'),
        ('avail', 'Availability')], required=True)
    to_read = fields.Boolean("To Read", default=True)
    internal_message = fields.Char("Internal Message", old_name='message')
    date_start = fields.Date("From", readonly=True)
    date_end = fields.Date("To", readonly=True)
    channel_object_id = fields.Char("Channel Object ID", old_name='wid', readonly=True)
    channel_message = fields.Char("Channel Message", old_name='wmessage', readonly=True)

    @api.multi
    def mark_readed(self):
        for record in self:
            record.to_read = False

    @api.multi
    def toggle_to_read(self):
        for record in self:
            record.to_read = not record.to_read

    @api.multi
    def mark_as_read(self):
        reserv_ids = []
        for record in self:
            if record.section == 'reservation' and record.channel_object_id:
                reserv_ids.append(record.channel_object_id)
                record.to_read = False
        if any(reserv_ids):
            res = self.env['hotel.channel.connector'].mark_bookings(reserv_ids)
            if not res:
                raise ValidationError(
                    ("Can't mark reservation as readed in Channel!"))

    @api.model
    def _needaction_domain_get(self):
        return [('to_read', '=', True)]
