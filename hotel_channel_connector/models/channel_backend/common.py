# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import os
import binascii
from contextlib import contextmanager
from odoo import models, api, fields
from ...components.backend_adapter import WuBookLogin, WuBookServer
_logger = logging.getLogger(__name__)

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
    security_token = fields.Char('Channel Service Security Token')

    reservation_id_str = fields.Char('Channel Reservation ID', store=False)

    avail_from = fields.Date('Availability From', store=False)
    avail_to = fields.Date('Availability To', store=False)

    restriction_from = fields.Date('Restriction From', store=False)
    restriction_to = fields.Date('Restriction To', store=False)
    restriction_id = fields.Many2one('channel.hotel.room.type.restriction',
                                     'Channel Restriction',
                                     store=False)

    pricelist_from = fields.Date('Pricelist From', store=False)
    pricelist_to = fields.Date('Pricelist To', store=False)
    pricelist_id = fields.Many2one('channel.product.pricelist',
                                   'Channel Product Pricelist',
                                   store=False)

    issue_ids = fields.One2many('hotel.channel.connector.issue',
                                'backend_id',
                                string='Issues')
    ota_ids = fields.One2many('channel.ota.info',
                              'backend_id',
                              string="OTA's")

    @api.multi
    def generate_key(self):
        for record in self:
            record.security_token = binascii.hexlify(os.urandom(32)).decode()

    @api.multi
    def import_reservations(self):
        channel_hotel_reservation_obj = self.env['channel.hotel.reservation']
        for backend in self:
            count = channel_hotel_reservation_obj.import_reservations(backend)
            if count == 0:
                self.env.user.notify_info("No reservations to import. All done :)",
                                          title="Import Reservations")
            else:
                self.env.user.notify_info("%d reservations successfully imported" % count,
                                          title="Import Reservations")
        return True

    @api.multi
    def import_reservation(self):
        channel_hotel_reservation_obj = self.env['channel.hotel.reservation']
        for backend in self:
            res = channel_hotel_reservation_obj.import_reservation(
                backend,
                backend.reservation_id_str)
            if not res:
                self.env.user.notify_warning(
                    "Can't import '%s' reservation" % backend.reservation_id_str,
                    title="Import Reservations")
        return True

    @api.multi
    def import_rooms(self):
        channel_hotel_room_type_obj = self.env['channel.hotel.room.type']
        for backend in self:
            count = channel_hotel_room_type_obj.import_rooms(backend)
            if count == 0:
                self.env.user.notify_info("No rooms to import. All done :)",
                                          title="Import Rooms")
            else:
                self.env.user.notify_info("%d rooms successfully imported" % count,
                                          title="Import Rooms")
        return True

    @api.multi
    def import_otas_info(self):
        channel_ota_info_obj = self.env['channel.ota.info']
        for backend in self:
            count = channel_ota_info_obj.import_otas_info(backend)
            self.env.user.notify_info("%d ota's successfully imported" % count,
                                      title="Import OTA's")
        return True

    @api.multi
    def import_availability(self):
        channel_hotel_room_type_avail_obj = self.env['channel.hotel.room.type.availability']
        for backend in self:
            res = channel_hotel_room_type_avail_obj.import_availability(
                backend,
                backend.avail_from,
                backend.avail_to)
            if not res:
                self.env.user.notify_warning("Error importing availability",
                                             title="Import Availability")
        return True

    @api.multi
    def push_availability(self):
        channel_hotel_room_type_avail_obj = self.env['channel.hotel.room.type.availability']
        for backend in self:
            res = channel_hotel_room_type_avail_obj.push_availability(backend)
            if not res:
                self.env.user.notify_warning("Error pushing availability",
                                             title="Export Availability")
        return True

    @api.multi
    def import_restriction_plans(self):
        channel_hotel_room_type_restr_obj = self.env['channel.hotel.room.type.restriction']
        for backend in self:
            count = channel_hotel_room_type_restr_obj.import_restriction_plans(backend)
            if count == 0:
                self.env.user.notify_info("No restiction plans to import. All done :)",
                                          title="Import Restrictions")
            else:
                self.env.user.notify_info("%d restriction plans successfully imported" % count,
                                          title="Import Restrictions")
        return True

    @api.multi
    def import_restriction_values(self):
        channel_hotel_restr_item_obj = self.env['channel.hotel.room.type.restriction.item']
        for backend in self:
            res = channel_hotel_restr_item_obj.import_restriction_values(
                backend,
                backend.restriction_from,
                backend.restriction_to,
                backend.restriction_id and backend.restriction_id.external_id or False)
            if not res:
                self.env.user.notify_warning("Error importing restrictions",
                                             title="Import Restrictions")
        return True

    @api.multi
    def push_restriction(self):
        channel_hotel_restr_item_obj = self.env['channel.hotel.room.type.restriction.item']
        for backend in self:
            res = channel_hotel_restr_item_obj.push_restriction(backend)
            if not res:
                self.env.user.notify_warning("Error pushing restrictions",
                                             title="Export Restrictions")
        return True

    @api.multi
    def import_pricelist_plans(self):
        channel_product_pricelist_obj = self.env['channel.product.pricelist']
        for backend in self:
            count = channel_product_pricelist_obj.import_price_plans(backend)
            if count == 0:
                self.env.user.notify_info("No pricelist plans to import. All done :)",
                                          title="Import Pricelists")
            else:
                self.env.user.notify_info("%d pricelist plans successfully imported" % count,
                                          title="Import Pricelists")
        return True

    @api.multi
    def import_pricelist_values(self):
        channel_product_pricelist_item_obj = self.env['channel.product.pricelist.item']
        for backend in self:
            res = channel_product_pricelist_item_obj.import_pricelist_values(
                backend,
                backend.pricelist_from,
                backend.pricelist_to,
                backend.pricelist_id and backend.pricelist_id.external_id or False)
            if not res:
                self.env.user.notify_warning("Error importing pricelists",
                                             title="Import Pricelists")
        return True

    @api.multi
    def push_pricelist(self):
        channel_product_pricelist_item_obj = self.env['channel.product.pricelist.item']
        for backend in self:
            res = channel_product_pricelist_item_obj.push_pricelist(backend)
            if not res:
                self.env.user.notify_warning("Error pushing pricelists",
                                             title="Export Pricelists")
        return True

    @api.model
    def cron_push_changes(self):
        backends = self.env[self._name].search([])
        backends.push_availability()
        backends.push_restriction()
        backends.push_pricelist()

    @api.model
    def cron_import_reservations(self):
        self.env[self._name].search([]).import_reservations()

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
