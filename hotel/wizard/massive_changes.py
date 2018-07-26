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
from datetime import datetime, timedelta
from openerp.exceptions import ValidationError
from openerp import models, fields, api
from openerp.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT)
from odoo.addons.hotel import date_utils


class MassiveChangesWizard(models.TransientModel):
    _name = 'hotel.wizard.massive.changes'

    # Common fields
    section = fields.Selection([
        ('0', 'Availability'),
        ('1', 'Restrictions'),
        ('2', 'Pricelist'),
    ], string='Section', default='0')
    date_start = fields.Datetime('Start Date', required=True)
    date_end = fields.Datetime('End Date', required=True)
    dmo = fields.Boolean('Monday', default=True)
    dtu = fields.Boolean('Tuesday', default=True)
    dwe = fields.Boolean('Wednesday', default=True)
    dth = fields.Boolean('Thursday', default=True)
    dfr = fields.Boolean('Friday', default=True)
    dsa = fields.Boolean('Saturday', default=True)
    dsu = fields.Boolean('Sunday', default=True)
    applied_on = fields.Selection([
        ('0', 'Global'),
        ('1', 'Virtual Room'),
    ], string='Applied On', default='0')
    # virtual_room_ids = fields.Many2many('hotel.virtual.room',
    #                                     string="Virtual Rooms")
    room_type_ids = fields.Many2many('hotel.room.type',
                                        string="Room Types")

    # Availability fields
    change_avail = fields.Boolean(default=False)
    avail = fields.Integer('Avail', default=0)
    change_no_ota = fields.Boolean(default=False)
    no_ota = fields.Boolean('No OTA', default=False)

    # Restriction fields
    restriction_id = fields.Many2one('hotel.virtual.room.restriction',
                                     'Restriction Plan')
    change_min_stay = fields.Boolean(default=False)
    min_stay = fields.Integer("Min. Stay")
    change_min_stay_arrival = fields.Boolean(default=False)
    min_stay_arrival = fields.Integer("Min. Stay Arrival")
    change_max_stay = fields.Boolean(default=False)
    max_stay = fields.Integer("Max. Stay")
    change_max_stay_arrival = fields.Boolean(default=False)
    max_stay_arrival = fields.Integer("Max. Stay Arrival")
    change_closed = fields.Boolean(default=False)
    closed = fields.Boolean('Closed')
    change_closed_departure = fields.Boolean(default=False)
    closed_departure = fields.Boolean('Closed Departure')
    change_closed_arrival = fields.Boolean(default=False)
    closed_arrival = fields.Boolean('Closed Arrival')

    # Pricelist fields
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist')
    price = fields.Char('Price', help="Can use '+','-' \
                                        or '%'...\nExamples:\n a) +12.3 \
                                        \t> Increase the price in 12.3\n \
                                        b) -1.45% \t> Substract 1.45%\n c) 45 \
                                        \t\t> Sets the price to 45")

    @api.onchange('date_start')
    def onchange_date_start(self):
        self.ensure_one()
        self.date_end = self.date_start

    @api.multi
    def is_valid_date(self, chkdate):
        self.ensure_one()
        date_start_dt = fields.Datetime.from_string(self.date_start)
        date_end_dt = fields.Datetime.from_string(self.date_end)
        wday = chkdate.timetuple()[6]
        wedays = (self.dmo, self.dtu, self.dwe, self.dth, self.dfr, self.dsa,
                  self.dsu)
        return (chkdate >= self.date_start and chkdate <= self.date_end
                and wedays[wday])

    @api.model
    def _save_prices(self, ndate, vrooms, record):
        product_pricelist_item_obj = self.env['product.pricelist.item']
        price = 0.0
        operation = 'a'
        if record.price[0] == '+' or record.price[0] == '-':
            if record.price[-1] == '%':
                price = float(record.price[1:-1])
                operation = (record.price[0] == '+') and 'ap' or 'sp'
            else:
                price = float(record.price[1:])
                operation = (record.price[0] == '+') and 'a' or 's'
        else:
            if record.price[-1] == '%':
                price = float(record.price[:-1])
                operation = 'np'
            else:
                price = float(record.price)
                operation = 'n'

        domain = [
            ('pricelist_id', '=', record.pricelist_id.id),
            ('date_start', '>=', ndate.strftime(
                                    DEFAULT_SERVER_DATE_FORMAT)),
            ('date_end', '<=', ndate.strftime(
                                    DEFAULT_SERVER_DATE_FORMAT)),
            ('compute_price', '=', 'fixed'),
            ('applied_on', '=', '1_product'),
        ]

        product_tmpl_ids = vrooms.mapped(
                                    'product_id.product_tmpl_id')
        for vroom in vrooms:
            prod_tmpl_id = vroom.product_id.product_tmpl_id
            pricelist_item_ids = product_pricelist_item_obj.search(
                domain+[('product_tmpl_id', '=', prod_tmpl_id.id)])
            if any(pricelist_item_ids):
                if operation != 'n':
                    for pli in pricelist_item_ids:
                        pli_price = pli.fixed_price
                        if operation == 'a':
                            pli.write({
                                'fixed_price': pli_price + price})
                        elif operation == 'ap':
                            pli.write({'fixed_price': pli_price + price * pli_price * 0.01})
                        elif operation == 's':
                            pli.write({
                                'fixed_price': pli_price - price})
                        elif operation == 'sp':
                            pli.write({'fixed_price': pli_price - price * pli_price * 0.01})
                        elif operation == 'np':
                            pli.write({'fixed_price': price * pli_price * 0.01})
                else:
                    pricelist_item_ids.write({'fixed_price': price})
            else:
                product_pricelist_item_obj.create({
                    'pricelist_id': record.pricelist_id.id,
                    'date_start': ndate.strftime(
                                    DEFAULT_SERVER_DATE_FORMAT),
                    'date_end': ndate.strftime(
                                    DEFAULT_SERVER_DATE_FORMAT),
                    'compute_price': 'fixed',
                    'applied_on': '1_product',
                    'product_tmpl_id': prod_tmpl_id.id,
                    'fixed_price': price,
                })

    @api.model
    def _get_restrictions_values(self, ndate, vroom, record):
        vals = {}
        if record.change_min_stay:
            vals.update({'min_stay': record.min_stay})
        if record.change_min_stay_arrival:
            vals.update({'min_stay_arrival': record.min_stay_arrival})
        if record.change_max_stay:
            vals.update({'max_stay': record.max_stay})
        if record.change_max_stay_arrival:
            vals.update({'max_stay_arrival': record.max_stay_arrival})
        if record.change_closed:
            vals.update({'closed': record.closed})
        if record.change_closed_departure:
            vals.update({'closed_departure': record.closed_departure})
        if record.change_closed_arrival:
            vals.update({'closed_arrival': record.closed_arrival})
        return vals

    @api.model
    def _save_restrictions(self, ndate, vrooms, record):
        hotel_vroom_re_it_obj = self.env['hotel.virtual.room.restriction.item']
        domain = [
            ('date_start', '>=', ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)),
            ('date_end', '<=', ndate.strftime(DEFAULT_SERVER_DATE_FORMAT)),
            ('restriction_id', '=', record.restriction_id.id),
            ('applied_on', '=', '0_virtual_room'),
        ]

        for vroom in vrooms:
            vals = self._get_restrictions_values(ndate, vroom, record)
            if not any(vals):
                continue

            rrest_item_ids = hotel_vroom_re_it_obj.search(
                domain+[('virtual_room_id', '=', vroom.id)])
            if any(rrest_item_ids):
                rrest_item_ids.write(vals)
            else:
                vals.update({
                    'date_start': ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'date_end': ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'restriction_id': record.restriction_id.id,
                    'virtual_room_id': vroom.id,
                    'applied_on': '0_virtual_room',
                })
                hotel_vroom_re_it_obj.create(vals)

    @api.model
    def _get_availability_values(self, ndate, vroom, record):
        hotel_vroom_obj = self.env['hotel.virtual.room']
        vals = {}
        if record.change_no_ota:
            vals.update({'no_ota': record.no_ota})
        if record.change_avail:
            cavail = len(hotel_vroom_obj.check_availability_virtual_room(
                ndate.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                ndate.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                virtual_room_id=vroom.id))
            vals.update({
                'avail': min(cavail, vroom.total_rooms_count, record.avail),
            })
        return vals

    @api.model
    def _save_availability(self, ndate, vrooms, record):
        hotel_vroom_obj = self.env['hotel.virtual.room']
        hotel_vroom_avail_obj = self.env['hotel.virtual.room.availability']
        domain = [('date', '=', ndate.strftime(DEFAULT_SERVER_DATE_FORMAT))]

        for vroom in vrooms:
            vals = self._get_availability_values(ndate, vroom, record)
            if not any(vals):
                continue

            vrooms_avail = hotel_vroom_avail_obj.search(
                domain+[('virtual_room_id', '=', vroom.id)]
            )
            if any(vrooms_avail):
                # Mail module want a singleton
                for vr_avail in vrooms_avail:
                    vr_avail.write(vals)
            else:
                vals.update({
                    'date': ndate.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    'virtual_room_id': vroom.id
                })
                hotel_vroom_avail_obj.with_context({
                    'mail_create_nosubscribe': True,
                }).create(vals)

    @api.multi
    def massive_change_close(self):
        self._do_massive_change()
        return True

    @api.multi
    def massive_change(self):
        self._do_massive_change()
        return {
            "type": "ir.actions.do_nothing",
        }

    @api.multi
    def _do_massive_change(self):
        hotel_vroom_obj = self.env['hotel.virtual.room']
        for record in self:
            date_start_dt = date_utils.get_datetime(record.date_start,
                                                    hours=False)
            # Use min '1' for same date
            diff_days = date_utils.date_diff(record.date_start,
                                             record.date_end,
                                             hours=False) + 1
            wedays = (record.dmo, record.dtu, record.dwe, record.dth,
                      record.dfr, record.dsa, record.dsu)
            vrooms = record.applied_on == '1' and record.room_type_id \
                or hotel_vroom_obj.search([])

            for i in range(0, diff_days):
                ndate = date_start_dt + timedelta(days=i)
                if not wedays[ndate.timetuple()[6]]:
                    continue

                if record.section == '0':
                    self._save_availability(ndate, vrooms, record)
                elif record.section == '1':
                    self._save_restrictions(ndate, vrooms, record)
                elif record.section == '2':
                    self._save_prices(ndate, vrooms, record)
        return True
