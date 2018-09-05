# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import binascii
import logging
from datetime import datetime, timedelta
from openerp import models, fields, api, _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.addons.hotel import date_utils
_logger = logging.getLogger(__name__)


class HotelChannelConnectorConfiguration(models.TransientModel):
    _inherit = 'res.config.settings'

    channel_push_security_token = fields.Char('WuBook Push Notification Security Token')

    @api.multi
    def set_values(self):
        super(HotelChannelConnectorConfiguration, self).set_values()

        self.env['ir.default'].sudo().set(
            'res.config.settings', 'channel_push_security_token',
            self.channel_push_security_token)

    @api.model
    def get_values(self):
        res = super(HotelChannelConnectorConfiguration, self).get_values()

        # ONLY FOR v11. DO NOT FORWARD-PORT
        channel_push_security_token = self.env['ir.default'].sudo().get(
            'res.config.settings', 'channel_push_security_token')
        res.update(
            channel_push_security_token=channel_push_security_token,
        )
        return res

    # Dangerus method: Usefull for cloned instances with new wubook account
    @api.multi
    def resync(self):
        self.ensure_one()

        now_utc_dt = date_utils.now()
        now_utc_str = now_utc_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)

        # Reset Issues
        issue_ids = self.env['wubook.issue'].search([])
        issue_ids.write({
            'to_read': False
        })

        # Push Virtual Rooms
        wubook_obj = self.env['wubook'].with_context({
            'init_connection': False
        })
        if wubook_obj.init_connection():
            ir_seq_obj = self.env['ir.sequence']
            vrooms = self.env['hotel.room.type'].search([])
            for vroom in vrooms:
                shortcode = ir_seq_obj.next_by_code('hotel.room.type')[:4]
                channel_room_id = wubook_obj.create_room(
                    shortcode,
                    vroom.name,
                    vroom.wcapacity,
                    vroom.list_price,
                    vroom.max_real_rooms
                )
                if channel_room_id:
                    vroom.with_context(wubook_action=False).write({
                        'channel_room_id': channel_room_id,
                        'wscode': shortcode,
                    })
                else:
                    vroom.with_context(wubook_action=False).write({
                        'channel_room_id': '',
                        'wscode': '',
                    })
            # Create Restrictions
            vroom_rest_obj = self.env['hotel.room.type.restriction']
            restriction_ids = vroom_rest_obj.search([])
            for restriction in restriction_ids:
                if restriction.wpid != '0':
                    channel_plan_id = wubook_obj.create_rplan(restriction.name)
                    restriction.write({
                        'channel_plan_id': channel_plan_id or ''
                    })
            # Create Pricelist
            pricelist_ids = self.env['product.pricelist'].search([])
            for pricelist in pricelist_ids:
                channel_plan_id = wubook_obj.create_plan(pricelist.name, pricelist.wdaily)
                pricelist.write({
                    'channel_plan_id': channel_plan_id or ''
                })
            wubook_obj.close_connection()

        # Reset Folios
        folio_ids = self.env['hotel.folio'].search([])
        folio_ids.with_context(wubook_action=False).write({
            'wseed': '',
        })

        # Reset Reservations
        reservation_ids = self.env['hotel.reservation'].search([
            ('channel_reservation_id', '!=', ''),
            ('channel_reservation_id', '!=', False)
        ])
        reservation_ids.with_context(wubook_action=False).write({
            'channel_reservation_id': '',
            'ota_id': False,
            'ota_reservation_id': '',
            'is_from_ota': False,
            'wstatus': 0
        })

        # Get Parity Models
        pricelist_id = int(self.env['ir.default'].sudo().get(
                            'res.config.settings', 'parity_pricelist_id'))
        restriction_id = int(self.env['ir.default'].sudo().get(
                            'res.config.settings', 'parity_restrictions_id'))

        vroom_restr_it_obj = self.env['hotel.room.type.restriction.item']
        # Secure Wubook Input
        restriction_item_ids = vroom_restr_it_obj.search([
            ('applied_on', '=', '0_room_type'),
            ('date_start', '<', now_utc_str),
        ])
        if any(restriction_item_ids):
            restriction_item_ids.with_context(wubook_action=False).write({
                'wpushed': True
            })
        # Put to push restrictions
        restriction_item_ids = vroom_restr_it_obj.search([
            ('restriction_id', '=', restriction_id),
            ('applied_on', '=', '0_room_type'),
            ('wpushed', '=', True),
            ('date_start', '>=', now_utc_str),
        ])
        if any(restriction_item_ids):
            restriction_item_ids.with_context(wubook_action=False).write({
                'wpushed': False
            })

        # Secure Wubook Input
        pricelist_item_ids = self.env['product.pricelist.item'].search([
            ('applied_on', '=', '1_product'),
            ('compute_price', '=', 'fixed'),
            ('date_start', '<', now_utc_str),
        ])
        if any(pricelist_item_ids):
            pricelist_item_ids.with_context(wubook_action=False).write({
                'wpushed': True
            })
        # Put to push pricelists
        pricelist_item_ids = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist_id),
            ('applied_on', '=', '1_product'),
            ('compute_price', '=', 'fixed'),
            ('wpushed', '=', True),
            ('date_start', '>=', now_utc_str),
        ])
        if any(pricelist_item_ids):
            pricelist_item_ids.with_context(wubook_action=False).write({
                'wpushed': False
            })

        # Secure Wubook Input
        availabity_ids = self.env['hotel.room.type.availability'].search([
            ('date', '<', now_utc_str),
        ])
        if any(availabity_ids):
            availabity_ids.with_context(wubook_action=False).write({
                'wpushed': True
            })
        # Put to push availability
        availabity_ids = self.env['hotel.room.type.availability'].search([
            ('wpushed', '=', True),
            ('date', '>=', now_utc_str),
        ])
        if any(availabity_ids):
            availabity_ids.with_context(wubook_action=False).write({
                'wpushed': False
            })

        # Generate Security Token
        self.env['ir.default'].sudo().set(
            'wubook.config.settings',
            'wubook_push_security_token',
            binascii.hexlify(os.urandom(16)).decode())
        self.env.cr.commit()    # FIXME: Need do this

        # Push Changes
        if wubook_obj.init_connection():
            wubook_obj.push_activation()
            wubook_obj.import_channels_info()
            wubook_obj.push_changes()
            wubook_obj.close_connection()
