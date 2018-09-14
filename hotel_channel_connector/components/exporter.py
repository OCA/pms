# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo.addons.component.core import AbstractComponent
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
from .backend_adapter import DEFAULT_WUBOOK_DATE_FORMAT
from odoo.addons.hotel import date_utils
from odoo import api
_logger = logging.getLogger(__name__)

class HotelChannelConnectorExporter(AbstractComponent):
    _name = 'hotel.channel.exporter'
    _inherit = ['base.exporter', 'base.hotel.channel.connector']
    _usage = 'channel.exporter'

    @api.model
    def push_changes(self):
        return self.push_availability() and self.push_priceplans() and \
                self.push_restrictions()

    @api.model
    def push_availability(self):
        room_type_avail_ids = self.env['hotel.room.type.availability'].search([
            ('wpushed', '=', False),
            ('date', '>=', date_utils.now(hours=False).strftime(
                DEFAULT_SERVER_DATE_FORMAT))
        ])

        room_types = room_type_avail_ids.mapped('room_type_id')
        avails = []
        for room_type in room_types:
            room_type_avails = room_type_avail_ids.filtered(
                lambda x: x.room_type_id.id == room_type.id)
            days = []
            for room_type_avail in room_type_avails:
                room_type_avail.with_context({
                    'wubook_action': False}).write({'wpushed': True})
                wavail = room_type_avail.avail
                if wavail > room_type_avail.wmax_avail:
                    wavail = room_type_avail.wmax_avail
                date_dt = date_utils.get_datetime(
                    room_type_avail.date,
                    dtformat=DEFAULT_SERVER_DATE_FORMAT)
                days.append({
                    'date': date_dt.strftime(DEFAULT_WUBOOK_DATE_FORMAT),
                    'avail': wavail,
                    'no_ota': room_type_avail.no_ota and 1 or 0,
                    # 'booked': room_type_avail.booked and 1 or 0,
                })
            avails.append({'id': room_type.wrid, 'days': days})
        _logger.info("UPDATING AVAILABILITY IN WUBOOK...")
        _logger.info(avails)
        if any(avails):
            self.backend_adapter.update_availability(avails)
        return True

    @api.model
    def push_priceplans(self):
        unpushed = self.env['product.pricelist.item'].search([
            ('wpushed', '=', False),
            ('date_start', '>=', date_utils.now(hours=False).strftime(
                DEFAULT_SERVER_DATE_FORMAT))
        ], order="date_start ASC")
        if any(unpushed):
            date_start = date_utils.get_datetime(
                unpushed[0].date_start,
                dtformat=DEFAULT_SERVER_DATE_FORMAT)
            date_end = date_utils.get_datetime(
                unpushed[-1].date_start,
                dtformat=DEFAULT_SERVER_DATE_FORMAT)
            days_diff = date_utils.date_diff(date_start, date_end, hours=False) + 1

            prices = {}
            pricelist_ids = self.env['product.pricelist'].search([
                ('wpid', '!=', False),
                ('active', '=', True)
            ])
            for pr in pricelist_ids:
                prices.update({pr.wpid: {}})
                unpushed_pl = self.env['product.pricelist.item'].search(
                    [('wpushed', '=', False), ('pricelist_id', '=', pr.id)])
                product_tmpl_ids = unpushed_pl.mapped('product_tmpl_id')
                for pt_id in product_tmpl_ids:
                    room_type = self.env['hotel.room.type'].search([
                        ('product_id.product_tmpl_id', '=', pt_id.id)
                    ], limit=1)
                    if room_type:
                        prices[pr.wpid].update({room_type.wrid: []})
                        for i in range(0, days_diff):
                            prod = room_type.product_id.with_context({
                                'quantity': 1,
                                'pricelist': pr.id,
                                'date': (date_start + timedelta(days=i)).
                                        strftime(DEFAULT_SERVER_DATE_FORMAT),
                                })
                            prices[pr.wpid][room_type.wrid].append(prod.price)
            _logger.info("UPDATING PRICES IN WUBOOK...")
            _logger.info(prices)
            for k_pk, v_pk in prices.iteritems():
                if any(v_pk):
                    self.backend_adapter.update_plan_prices(k_pk, date_start.strftime(
                        DEFAULT_SERVER_DATE_FORMAT), v_pk)

            unpushed.with_context({
                'wubook_action': False}).write({'wpushed': True})
        return True

    @api.model
    def push_restrictions(self):
        room_type_rest_obj = self.env['hotel.room.type.restriction']
        rest_item_obj = self.env['hotel.room.type.restriction.item']
        unpushed = rest_item_obj.search([
            ('wpushed', '=', False),
            ('date_start', '>=', date_utils.now(hours=False).strftime(
                DEFAULT_SERVER_DATE_FORMAT))
        ], order="date_start ASC")
        if any(unpushed):
            date_start = date_utils.get_datetime(
                unpushed[0].date_start,
                dtformat=DEFAULT_SERVER_DATE_FORMAT)
            date_end = date_utils.get_datetime(
                unpushed[-1].date_start,
                dtformat=DEFAULT_SERVER_DATE_FORMAT)
            days_diff = date_utils.date_diff(
                date_start,
                date_end,
                hours=False) + 1
            restrictions = {}
            restriction_plan_ids = room_type_rest_obj.search([
                ('wpid', '!=', False),
                ('active', '=', True)
            ])
            for rp in restriction_plan_ids:
                restrictions.update({rp.wpid: {}})
                unpushed_rp = rest_item_obj.search([
                    ('wpushed', '=', False),
                    ('restriction_id', '=', rp.id)
                ])
                room_type_ids = unpushed_rp.mapped('room_type_id')
                for room_type in room_type_ids:
                    restrictions[rp.wpid].update({room_type.wrid: []})
                    for i in range(0, days_diff):
                        ndate_dt = date_start + timedelta(days=i)
                        restr = room_type.get_restrictions(
                            ndate_dt.strftime(DEFAULT_SERVER_DATE_FORMAT))
                        if restr:
                            restrictions[rp.wpid][room_type.wrid].append({
                                'min_stay': restr.min_stay or 0,
                                'min_stay_arrival': restr.min_stay_arrival or 0,
                                'max_stay': restr.max_stay or 0,
                                'max_stay_arrival': restr.max_stay_arrival or 0,
                                'closed': restr.closed and 1 or 0,
                                'closed_arrival': restr.closed_arrival and 1 or 0,
                                'closed_departure': restr.closed_departure and 1 or 0,
                            })
                        else:
                            restrictions[rp.wpid][room_type.wrid].append({})
            _logger.info("UPDATING RESTRICTIONS IN WUBOOK...")
            _logger.info(restrictions)
            for k_res, v_res in restrictions.iteritems():
                if any(v_res):
                    self.backend_adapter.update_rplan_values(
                        int(k_res),
                        date_start.strftime(DEFAULT_SERVER_DATE_FORMAT),
                        v_res)
            unpushed.with_context({
                'wubook_action': False}).write({'wpushed': True})
        return True
