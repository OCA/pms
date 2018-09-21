# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from contextlib import contextmanager
from odoo import models, api, fields
from ...components.backend_adapter import WuBookLogin, WuBookServer

class ChannelBackend(models.Model):
    _name = 'channel.backend'
    _description = 'Hotel Channel Backend'
    _inherit = 'connector.backend'

    @api.model
    def select_versions(self):
        """ Available versions in the backend.
        Can be inherited to add custom versions.  Using this method
        to add a version from an ``_inherit`` does not constrain
        to redefine the ``version`` field in the ``_inherit`` model.
        """
        return [('1.2', '1.2+')]

    name = fields.Char('Name')
    version = fields.Selection(selection='select_versions', required=True)
    username = fields.Char('Channel Service Username')
    passwd = fields.Char('Channel Service Password')
    lcode = fields.Char('Channel Service lcode')
    server = fields.Char('Channel Service Server',
                         default='https://wired.wubook.net/xrws/')
    pkey = fields.Char('Channel Service PKey')

    @api.multi
    def import_reservations(self):
        channel_hotel_reservation = self.env['channel.hotel.reservation']
        for backend in self:
            channel_hotel_reservation.import_reservations(backend)
        return True

    @api.multi
    def import_rooms(self):
        channel_hotel_room_type = self.env['channel.hotel.room.type']
        for backend in self:
            channel_hotel_room_type.import_rooms(backend)
        return True

    @contextmanager
    @api.multi
    def work_on(self, model_name, **kwargs):
        self.ensure_one()
        wubook_login = WuBookLogin(
            self.server,
            self.username,
            self.passwd,
            self.lcode,
            self.pkey)
        with WuBookServer(wubook_login) as channel_api:
            _super = super(ChannelBackend, self)
            with _super.work_on(model_name, channel_api=channel_api, **kwargs) as work:
                yield work
