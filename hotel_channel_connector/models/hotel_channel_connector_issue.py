# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2017 Solucións Aloxa S.L. <info@aloxa.eu>
#                       Alexandre Díaz <dev@redneboa.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
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
    channel_name = fields.Char("Channel Name")
    to_read = fields.Boolean("To Read", default=True)
    internal_message = fields.Char("Internal Message", old_name='message')
    date_start = fields.Date("From", readonly=True)
    date_end = fields.Date("To", readonly=True)
    channel_object_id = fields.Char("Channel Object ID", old_name='wid', readonly=True)
    channel_connector_message = fields.Char("Channel Connector Message",
                                            old_name='wmessage', readonly=True)

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
