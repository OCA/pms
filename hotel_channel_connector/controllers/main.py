# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from openerp import http, _
from openerp.http import request
from openerp.exceptions import ValidationError
_logger = logging.getLogger(__name__)


class website_wubook(http.Controller):
    # Called when created a reservation in wubook
    @http.route(['/wubook/push/reservations/<string:security_token>'],
                type='http', cors="*", auth="public", methods=['POST'],
                website=True, csrf=False)
    def wubook_push_reservations(self, security_token, **kwargs):
        # Check Security Token
        hotel_security_token = request.env['ir.default'].sudo().get(
                        'wubook.config.settings', 'wubook_push_security_token')
        if security_token != hotel_security_token:
            # _logger.info("Invalid Tokens: '%s' != '%s'" %
            #              (security_token, hotel_security_token))
            raise ValidationError(_('Invalid Security Token!'))

        rcode = kwargs.get('rcode')
        lcode = kwargs.get('lcode')

        # Correct Input?
        if not lcode or not rcode:
            raise ValidationError(_('Invalid Input Parameters!'))

        # WuBook Check
        if rcode == '2000' and lcode == '1000':
            return request.make_response(
                                    '200 OK', [('Content-Type', 'text/plain')])

        # Poor Security Check
        wlcode = request.env['ir.default'].sudo().get(
                                    'wubook.config.settings', 'wubook_lcode')
        if lcode != wlcode:
            raise ValidationError(_("Error! lcode doesn't match!"))

        _logger.info(_("[WUBOOK->ODOO] Importing Booking..."))
        # Create Reservation
        request.env['wubook'].sudo().fetch_booking(lcode, rcode)

        return request.make_response('200 OK',
                                     [('Content-Type', 'text/plain')])

    # Called when modify room values (Delay: ~5mins)
    @http.route(['/wubook/push/rooms/<string:security_token>'], type='http',
                cors="*", auth="public", methods=['POST'], website=True,
                csrf=False)
    def wubook_push_rooms(self, security_token, **kwargs):
        # Check Security Token
        hotel_security_token = request.env['ir.default'].sudo().get(
                        'wubook.config.settings', 'wubook_push_security_token')
        if security_token != hotel_security_token:
            # _logger.info("Invalid Tokens: '%s' != '%s'" %
            #              (security_token, hotel_security_token))
            raise ValidationError(_('Invalid Security Token!'))

        lcode = kwargs.get('lcode')
        dfrom = kwargs.get('dfrom')
        dto = kwargs.get('dto')

        # Correct Input?
        if not lcode or not dfrom or not dto:
            raise ValidationError(_('Invalid Input Parameters!'))

        # Poor Security Check
        wlcode = request.env['ir.default'].sudo().get(
                                    'wubook.config.settings', 'wubook_lcode')
        if lcode != wlcode:
            raise ValidationError(_("Error! lcode doesn't match!"))

        _logger.info(_("[WUBOOK->ODOO] Updating values..."))
        wubook_obj = request.env['wubook'].sudo().with_context({
            'init_connection': False
        })
        if wubook_obj.init_connection():
            wubook_obj.fetch_rooms_values(dfrom, dto)

            parity_restr_id = request.env['ir.default'].sudo().get(
                            'res.config.settings', 'parity_restrictions_id')
            if parity_restr_id:
                vroom_restr_obj = request.env['hotel.virtual.room.restriction']
                restr_id = vroom_restr_obj.sudo().browse(int(parity_restr_id))
                if restr_id and restr_id.wpid and restr_id.wpid != '0':
                    wubook_obj.fetch_rplan_restrictions(dfrom, dto,
                                                        rpid=restr_id.wpid)

            parity_pricelist_id = request.env['ir.default'].sudo().get(
                                'res.config.settings', 'parity_pricelist_id')
            if parity_pricelist_id:
                pricelist_id = request.env['product.pricelist'].sudo().browse(
                                                    int(parity_pricelist_id))
                if pricelist_id and pricelist_id.wpid:
                    wubook_obj.fetch_plan_prices(pricelist_id.wpid, dfrom, dto)
            wubook_obj.close_connection()

        return request.make_response('200 OK',
                                     [('Content-Type', 'text/plain')])
