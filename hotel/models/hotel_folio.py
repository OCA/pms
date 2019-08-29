# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
import time
import pytz
import logging
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from odoo.exceptions import except_orm, UserError, ValidationError
from odoo.tools import (
    misc,
    float_is_zero,
    float_compare,
    DEFAULT_SERVER_DATETIME_FORMAT,
    DEFAULT_SERVER_DATE_FORMAT)
from odoo import models, fields, api, _
_logger = logging.getLogger(__name__)

from odoo.addons import decimal_precision as dp


class HotelFolio(models.Model):
    _name = 'hotel.folio'
    _description = 'Hotel Folio'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'id'

    @api.model
    def _default_diff_invoicing(self):
        """
        If the guest has an invoicing address set,
        this method return diff_invoicing = True, else, return False
        """
        if 'folio_id' in self.env.context:
            folio = self.env['hotel.folio'].browse([
                self.env.context['folio_id']
            ])
        if folio.partner_id.id == folio.partner_invoice_id.id:
            return False
        return True

    @api.depends('state', 'room_lines.invoice_status', 'service_ids.invoice_status')
    def _get_invoiced(self):
        """
        Compute the invoice status of a Folio. Possible statuses:
        - no: if the Folio is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also the default value if the conditions of no other status is met.
        - to invoice: if any Folio line is 'to invoice', the whole Folio is 'to invoice'
        - invoiced: if all Folio lines are invoiced, the Folio is invoiced.

        The invoice_ids are obtained thanks to the invoice lines of the Folio lines, and we also search
        for possible refunds created directly from existing invoices. This is necessary since such a
        refund is not directly linked to the Folio.
        """
        for folio in self:
            invoice_ids = folio.room_lines.mapped('invoice_line_ids').mapped('invoice_id').filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
            invoice_ids |= folio.service_ids.mapped('invoice_line_ids').mapped('invoice_id').filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
            # Search for invoices which have been 'cancelled' (filter_refund = 'modify' in
            # 'account.invoice.refund')
            # use like as origin may contains multiple references (e.g. 'SO01, SO02')
            refunds = invoice_ids.search([('origin', 'like', folio.name), ('company_id', '=', folio.company_id.id)]).filtered(lambda r: r.type in ['out_invoice', 'out_refund'])
            invoice_ids |= refunds.filtered(lambda r: folio.id in r.folio_ids.ids)
            # Search for refunds as well
            refund_ids = self.env['account.invoice'].browse()
            if invoice_ids:
                for inv in invoice_ids:
                    refund_ids += refund_ids.search([('type', '=', 'out_refund'), ('origin', '=', inv.number), ('origin', '!=', False), ('journal_id', '=', inv.journal_id.id)])

            # Ignore the status of the deposit product
            deposit_product_id = self.env['sale.advance.payment.inv']._default_product_id()
            service_invoice_status = [service.invoice_status for service in folio.service_ids if service.product_id != deposit_product_id]
            reservation_invoice_status = [reservation.invoice_status for reservation in folio.room_lines]

            if folio.state not in ('confirm', 'done'):
                invoice_status = 'no'
            elif any(invoice_status == 'to invoice' for invoice_status in service_invoice_status) or \
                    any(invoice_status == 'to invoice' for invoice_status in reservation_invoice_status):
                invoice_status = 'to invoice'
            elif all(invoice_status == 'invoiced' for invoice_status in service_invoice_status) or \
                    any(invoice_status == 'invoiced' for invoice_status in reservation_invoice_status):
                invoice_status = 'invoiced'
            else:
                invoice_status = 'no'

            folio.update({
                'invoice_count': len(set(invoice_ids.ids + refund_ids.ids)),
                'invoice_ids': invoice_ids.ids + refund_ids.ids,
                'invoice_status': invoice_status
            })

    @api.model
    def _get_default_team(self):
        return self.env['crm.team']._get_default_team_id()

    #Main Fields--------------------------------------------------------
    name = fields.Char('Folio Number', readonly=True, index=True,
                       default=lambda self: _('New'))
    client_order_ref = fields.Char(string='Customer Reference', copy=False)
    partner_id = fields.Many2one('res.partner',
                                 track_visibility='onchange',
                                 ondelete='restrict',)

    room_lines = fields.One2many('hotel.reservation', 'folio_id',
                                 readonly=False,
                                 states={'done': [('readonly', True)]},
                                 help="Hotel room reservation detail.",)

    service_ids = fields.One2many('hotel.service', 'folio_id',
                                  readonly=False,
                                  states={'done': [('readonly', True)]},
                                  help="Hotel services detail provide to "
                                  "customer and it will include in "
                                  "main Invoice.")
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('hotel.folio'))
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="The analytic account related to a folio.", copy=False)
    currency_id = fields.Many2one('res.currency', related='pricelist_id.currency_id',
                                  string='Currency', readonly=True, required=True, ondelete='restrict',)

    pricelist_id = fields.Many2one('product.pricelist',
                                   string='Pricelist',
                                   required=True,
                                   ondelete='restrict',
                                   states={'draft': [('readonly', False)],
                                           'sent': [('readonly', False)]},
                                   help="Pricelist for current folio.")
    reservation_type = fields.Selection([('normal', 'Normal'),
                                         ('staff', 'Staff'),
                                         ('out', 'Out of Service')],
                                        'Type', default=lambda *a: 'normal')
    channel_type = fields.Selection([
        ('door', 'Door'),
        ('mail', 'Mail'),
        ('phone', 'Phone'),
        ('call', 'Call Center'),
        ('web', 'Web'),
        ('agency', 'Agencia'),
        ('operator', 'Tour operador'),
        ('virtualdoor', 'Virtual Door'),], 'Sales Channel', default='door')
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, ondelete='restrict',
                              track_visibility='onchange', default=lambda self: self.env.user)
    tour_operator_id = fields.Many2one('res.partner',
                                       'Tour Operator',
                                       ondelete='restrict',
                                       domain=[('is_tour_operator', '=', True)])
    date_order = fields.Datetime(
        string='Order Date',
        required=True, readonly=True, index=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        copy=False, default=fields.Datetime.now)
    confirmation_date = fields.Datetime(string='Confirmation Date', readonly=True, index=True, help="Date on which the folio is confirmed.", copy=False)
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('confirm', 'Confirmed'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ], string='Status',
        readonly=True, copy=False,
        index=True, track_visibility='onchange',
        default='draft')


    # Partner fields for being used directly in the Folio views---------
    email = fields.Char('E-mail', related='partner_id.email')
    mobile = fields.Char('Mobile', related='partner_id.mobile')
    phone = fields.Char('Phone', related='partner_id.phone')
    partner_internal_comment = fields.Text(string='Internal Partner Notes',
                                           related='partner_id.comment')

    #Payment Fields-----------------------------------------------------
    payment_ids = fields.One2many('account.payment', 'folio_id',
                                  readonly=True)
    return_ids = fields.One2many('payment.return', 'folio_id',
                                 readonly=True)
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', oldname='payment_term')
    credit_card_details = fields.Text('Credit Card Details')

    #Amount Fields------------------------------------------------------
    pending_amount = fields.Monetary(compute='compute_amount',
                                     store=True,
                                     string="Pending in Folio")
    refund_amount = fields.Monetary(compute='compute_amount',
                                    store=True,
                                    string="Payment Returns")
    invoices_paid = fields.Monetary(compute='compute_amount',
                                    store=True, track_visibility='onchange',
                                    string="Payments")
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True,
                                     readonly=True, compute='_amount_all',
                                     track_visibility='onchange')
    amount_tax = fields.Monetary(string='Taxes', store=True,
                                 readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True,
                                   compute='_amount_all', track_visibility='always')

    #Checkin Fields-----------------------------------------------------
    checkin_partner_ids = fields.One2many('hotel.checkin.partner', 'folio_id')
    booking_pending = fields.Integer('Booking pending',
                                     compute='_compute_checkin_partner_count')
    checkin_partner_count = fields.Integer('Checkin counter',
                                  compute='_compute_checkin_partner_count')
    checkin_partner_pending_count = fields.Integer('Checkin Pending',
                                          compute='_compute_checkin_partner_count')

    #Invoice Fields-----------------------------------------------------
    invoice_count = fields.Integer(compute='_get_invoiced')
    invoice_ids = fields.Many2many('account.invoice', string='Invoices',
                                   compute='_get_invoiced', readonly=True, copy=False)
    invoice_status = fields.Selection([('invoiced', 'Fully Invoiced'),
                                       ('to invoice', 'To Invoice'),
                                       ('no', 'Nothing to Invoice')],
                                      string='Invoice Status',
                                      compute='_get_invoiced',
                                      store=True, readonly=True, default='no')
    partner_invoice_id = fields.Many2one('res.partner',
                                         string='Invoice Address', required=True,
                                         states={'done': [('readonly', True)]},
                                         help="Invoice address for current sales order.")
    partner_invoice_vat = fields.Char(related="partner_invoice_id.vat")
    partner_invoice_name = fields.Char(related="partner_invoice_id.name")
    partner_invoice_street = fields.Char(related="partner_invoice_id.street")
    partner_invoice_street2 = fields.Char(related="partner_invoice_id.street")
    partner_invoice_zip = fields.Char(related="partner_invoice_id.zip")
    partner_invoice_city = fields.Char(related="partner_invoice_id.city")
    partner_invoice_state_id = fields.Many2one(related="partner_invoice_id.state_id")
    partner_invoice_country_id = fields.Many2one(related="partner_invoice_id.country_id")
    partner_invoice_email = fields.Char(related="partner_invoice_id.email")
    partner_invoice_lang  = fields.Selection(related="partner_invoice_id.lang")
    partner_parent_id  = fields.Many2one(related="partner_id.parent_id")
    fiscal_position_id = fields.Many2one('account.fiscal.position', oldname='fiscal_position', string='Fiscal Position')

    #WorkFlow Mail Fields-----------------------------------------------
    has_confirmed_reservations_to_send = fields.Boolean(
        compute='_compute_has_confirmed_reservations_to_send')
    has_cancelled_reservations_to_send = fields.Boolean(
        compute='_compute_has_cancelled_reservations_to_send')
    has_checkout_to_send = fields.Boolean(
        compute='_compute_has_checkout_to_send')

    #Generic Fields-----------------------------------------------------
    internal_comment = fields.Text(string='Internal Folio Notes')
    cancelled_reason = fields.Text('Cause of cancelled')
    closure_reason_id = fields.Many2one('room.closure.reason')
    prepaid_warning_days = fields.Integer(
        'Prepaid Warning Days',
        help='Margin in days to create a notice if a payment \
                advance has not been recorded')
    segmentation_ids = fields.Many2many('res.partner.category',
                                        string='Segmentation',
                                        ondelete='restrict')
    client_order_ref = fields.Char(string='Customer Reference', copy=False)
    note = fields.Text('Terms and conditions')
    sequence = fields.Integer(string='Sequence', default=10)
    team_id = fields.Many2one('crm.team',
                              'Sales Channel',
                              ondelete='restrict',
                              change_default=True,
                              default=_get_default_team,
                              oldname='section_id')

    @api.depends('room_lines.price_total', 'service_ids.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for record in self:
            amount_untaxed = amount_tax = 0.0
            amount_untaxed = sum(record.room_lines.mapped('price_subtotal')) + \
                sum(record.service_ids.mapped('price_subtotal'))
            amount_tax = sum(record.room_lines.mapped('price_tax')) + \
                sum(record.service_ids.mapped('price_tax'))
            record.update({
                'amount_untaxed': record.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': record.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.depends('amount_total', 'payment_ids', 'return_ids',
                 'reservation_type', 'state')
    @api.multi
    def compute_amount(self):
        acc_pay_obj = self.env['account.payment']
        for record in self:
            if record.reservation_type in ('staff', 'out'):
                vals = {
                    'pending_amount': 0,
                    'invoices_paid': 0,
                    'refund_amount': 0,
                }
                record.update(vals)
            else:
                total_inv_refund = 0
                payments = acc_pay_obj.search([
                    ('folio_id', '=', record.id)
                ])
                total_paid = sum(pay.amount for pay in payments)
                return_lines = self.env['payment.return.line'].search([
                    ('move_line_ids', 'in', payments.mapped('move_line_ids.id')),
                    ('return_id.state', '=', 'done')
                    ])
                total_inv_refund = sum(pay_return.amount for pay_return in return_lines)
                total = record.amount_total
                # REVIEW: Must We ignored services in cancelled folios pending amount?
                if record.state == 'cancelled':
                    total = total - sum(record.service_ids.mapped('price_total'))
                vals = {
                    'pending_amount': total - total_paid + total_inv_refund,
                    'invoices_paid': total_paid,
                    'refund_amount': total_inv_refund,
                }
                record.update(vals)

    @api.multi
    def action_pay(self):
        self.ensure_one()
        partner = self.partner_id.id
        amount = self.pending_amount
        view_id = self.env.ref('hotel.account_payment_view_form_folio').id
        return{
            'name': _('Register Payment'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.payment',
            'type': 'ir.actions.act_window',
            'view_id': view_id,
            'context': {
                'default_folio_id': self.id,
                'default_amount': amount,
                'default_payment_type': 'inbound',
                'default_partner_type': 'customer',
                'default_partner_id': partner,
                'default_communication': self.name,
            },
            'target': 'new',
        }

    @api.multi
    def open_invoices_folio(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def action_return_payments(self):
        self.ensure_one()
        return_move_ids = []
        acc_pay_obj = self.env['account.payment']
        payments = acc_pay_obj.search([
            '|',
            ('invoice_ids', 'in', self.invoice_ids.ids),
            ('folio_id', '=', self.id)
        ])
        return_move_ids += self.invoice_ids.filtered(
            lambda invoice: invoice.type == 'out_refund').mapped(
                'payment_move_line_ids.move_id.id')
        return_lines = self.env['payment.return.line'].search([
            ('move_line_ids', 'in', payments.mapped('move_line_ids.id')),
        ])
        return_move_ids += return_lines.mapped('return_id.move_id.id')

        return{
            'name': _('Returns'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', return_move_ids)],
        }

    @api.multi
    def go_to_currency_exchange(self):
        '''
         when Money Exchange button is clicked then this method is called.
        -------------------------------------------------------------------
        @param self: object pointer
        '''
        _logger.info('go_to_currency_exchange')
        pass
        # cr, uid, context = self.env.args
        # context = dict(context)
        # for rec in self:
        #     if rec.partner_id.id and len(rec.room_lines) != 0:
        #         context.update({'folioid': rec.id, 'guest': rec.partner_id.id,
        #                         'room_no': rec.room_lines[0].product_id.name})
        #         self.env.args = cr, uid, misc.frozendict(context)
        #     else:
        #         raise except_orm(_('Warning'), _('Please Reserve Any Room.'))
        # return {'name': _('Currency Exchange'),
        #         'res_model': 'currency.exchange',
        #         'type': 'ir.actions.act_window',
        #         'view_id': False,
        #         'view_mode': 'form,tree',
        #         'view_type': 'form',
        #         'context': {'default_folio_no': context.get('folioid'),
        #                     'default_hotel_id': context.get('hotel'),
        #                     'default_guest_name': context.get('guest'),
        #                     'default_room_number': context.get('room_no')
        #                     },
        #         }

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New') or 'name' not in vals:
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(
                    force_company=vals['company_id']
                ).next_by_code('hotel.folio') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('hotel.folio') or _('New')
        vals.update(self._prepare_add_missing_fields(vals))
        result = super(HotelFolio, self).create(vals)
        return result

    @api.model
    def _prepare_add_missing_fields(self, values):
        """ Deduce missing required fields from the onchange """
        res = {}
        onchange_fields = ['partner_invoice_id',
                           'pricelist_id',
                           'payment_term_id']
        if values.get('partner_id'):
            line = self.new(values)
            if any(f not in values for f in onchange_fields):
                line.onchange_partner_id()
            for field in onchange_fields:
                if field not in values:
                    res[field] = line._fields[field].convert_to_write(line[field], line)
        return res

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
            })
            return

        addr = self.partner_id.address_get(['invoice'])
        pricelist = self.partner_id.property_product_pricelist and \
            self.partner_id.property_product_pricelist.id or \
            self.env['ir.default'].sudo().get('res.config.settings', 'default_pricelist_id')
        values = {
            'pricelist_id': pricelist,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'user_id': self.partner_id.user_id.id or self.env.uid,
        }

        if self.env['ir.config_parameter'].sudo().get_param('sale.use_sale_note') and \
            self.env.user.company_id.sale_note:
            values['note'] = self.with_context(
                lang=self.partner_id.lang).env.user.company_id.sale_note

        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id.id
        self.update(values)

    @api.multi
    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self):
        values = {'reservation_type': self.env['hotel.folio'].\
                  calcule_reservation_type(
                      self.pricelist_id.is_staff,
                      self.reservation_type
                  )}
        self.update(values)

    @api.model
    def calcule_reservation_type(self, is_staff, current_type):
        if current_type == 'out':
            return 'out'
        elif is_staff:
            return 'staff'
        else:
            return 'normal'

    '''
    WORKFLOW STATE
    '''

    @api.multi
    def button_dummy(self):
        '''
        @param self: object pointer
        '''
        # for folio in self:
        #     folio.order_id.button_dummy()
        return True

    @api.multi
    def action_done(self):
        room_lines = self.mapped('room_lines')
        for line in room_lines:
            if line.state == "booking":
                line.action_reservation_checkout()

    @api.multi
    def action_cancel(self):
        for folio in self:
            for reservation in folio.room_lines.filtered(lambda res:
                                                         res.state != 'cancelled'):
                reservation.action_cancel()
            self.write({
                'state': 'cancel',
            })
        return True

    @api.multi
    def print_quotation(self):
        pass
        # TODO- New report to reservation order
        # self.order_id.filtered(lambda s: s.state == 'draft').write({
        #     'state': 'sent',
        # })
        # return self.env.ref('sale.report_saleorder').report_action(self, data=data)

    @api.multi
    def action_confirm(self):
        for folio in self.filtered(lambda folio: folio.partner_id not in folio.message_partner_ids):
            folio.message_subscribe([folio.partner_id.id])
        self.write({
            'state': 'confirm',
            'confirmation_date': fields.Datetime.now()
        })

        # if self.env.context.get('send_email'):
            # self.force_quotation_send()

        # create an analytic account if at least an expense product
        # if any([expense_policy != 'no' for expense_policy in self.order_line.mapped('product_id.expense_policy')]):
            # if not self.analytic_account_id:
                # self._create_analytic_account()

        return True


    """
    CHECKIN/OUT PROCESS
    """
    @api.multi
    def action_checks(self):
        self.ensure_one()
        rooms = self.mapped('room_lines.id')
        return {
            'name': _('Checkins'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'hotel.checkin.partner',
            'type': 'ir.actions.act_window',
            'domain': [('reservation_id', 'in', rooms)],
            'target': 'new',
        }

    @api.multi
    def _compute_checkin_partner_count(self):
        for record in self:
            if record.reservation_type == 'normal' and record.room_lines:
                write_vals = {}
                filtered_reservs = record.room_lines.filtered(
                    lambda x: x.state != 'cancelled' and \
                        not x.parent_reservation)
                mapped_checkin_partner = filtered_reservs.mapped('checkin_partner_ids.id')
                record.checkin_partner_count = len(mapped_checkin_partner)
                mapped_checkin_partner_count = filtered_reservs.mapped(
                    lambda x: (x.adults + x.children) - len(x.checkin_partner_ids))
                record.checkin_partner_pending_count = sum(mapped_checkin_partner_count)

    """
    MAILING PROCESS
    """

    @api.depends('room_lines')
    def _compute_has_confirmed_reservations_to_send(self):
        has_to_send = False
        if self.reservation_type != 'out':
            for rline in self.room_lines:
                if rline.splitted:
                    master_reservation = rline.parent_reservation or rline
                    has_to_send = self.env['hotel.reservation'].search_count([
                        ('splitted', '=', True),
                        ('folio_id', '=', self.id),
                        ('to_send', '=', True),
                        ('state', 'in', ('confirm', 'booking')),
                        '|',
                        ('parent_reservation', '=', master_reservation.id),
                        ('id', '=', master_reservation.id),
                    ]) > 0
                elif rline.to_send and rline.state in ('confirm', 'booking'):
                    has_to_send = True
                    break
            self.has_confirmed_reservations_to_send = has_to_send
        else:
            self.has_confirmed_reservations_to_send = False

    @api.depends('room_lines')
    def _compute_has_cancelled_reservations_to_send(self):
        has_to_send = False
        if self.reservation_type != 'out':
            for rline in self.room_lines:
                if rline.splitted:
                    master_reservation = rline.parent_reservation or rline
                    has_to_send = self.env['hotel.reservation'].search_count([
                        ('splitted', '=', True),
                        ('folio_id', '=', self.id),
                        ('to_send', '=', True),
                        ('state', '=', 'cancelled'),
                        '|',
                        ('parent_reservation', '=', master_reservation.id),
                        ('id', '=', master_reservation.id),
                    ]) > 0
                elif rline.to_send and rline.state == 'cancelled':
                    has_to_send = True
                    break
            self.has_cancelled_reservations_to_send = has_to_send
        else:
            self.has_cancelled_reservations_to_send = False

    @api.depends('room_lines')
    def _compute_has_checkout_to_send(self):
        has_to_send = True
        if self.reservation_type != 'out':
            for rline in self.room_lines:
                if rline.splitted:
                    master_reservation = rline.parent_reservation or rline
                    nreservs = self.env['hotel.reservation'].search_count([
                        ('splitted', '=', True),
                        ('folio_id', '=', self.id),
                        ('to_send', '=', True),
                        ('state', '=', 'done'),
                        '|',
                        ('parent_reservation', '=', master_reservation.id),
                        ('id', '=', master_reservation.id),
                    ])
                    if nreservs != len(self.room_lines):
                        has_to_send = False
                elif not rline.to_send or rline.state != 'done':
                    has_to_send = False
                    break
            self.has_checkout_to_send = has_to_send
        else:
            self.has_checkout_to_send = False

    @api.multi
    def send_reservation_mail(self):
        '''
        This function opens a window to compose an email,
        template message loaded by default.
        @param self: object pointer
        '''
        # Debug Stop -------------------
        # import wdb; wdb.set_trace()
        # Debug Stop -------------------
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference(
                'hotel',
                'mail_template_hotel_reservation')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(
                'mail',
                'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'hotel.folio',
            'default_res_id': self._ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_send': True,
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
            'force_send': True
        }

    @api.multi
    def send_exit_mail(self):
        '''
        This function opens a window to compose an email,
        template message loaded by default.
        @param self: object pointer
        '''
        # Debug Stop -------------------
        # import wdb; wdb.set_trace()
        # Debug Stop -------------------
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference(
                'hotel',
                'mail_template_hotel_exit')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(
                'mail',
                'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'hotel.reservation',
            'default_res_id': self._ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_send': True,
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
            'force_send': True
        }


    @api.multi
    def send_cancel_mail(self):
        '''
        This function opens a window to compose an email,
        template message loaded by default.
        @param self: object pointer
        '''
        # Debug Stop -------------------
        #import wdb; wdb.set_trace()
        # Debug Stop -------------------
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference(
                'hotel',
                'mail_template_hotel_cancel')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(
                'mail',
                'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'hotel.reservation',
            'default_res_id': self._ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_send': True,
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
            'force_send': True
        }

    @api.model
    def reservation_reminder_24hrs(self):
        """
        This method is for scheduler
        every 1day scheduler will call this method to
        find all tomorrow's reservations.
        ----------------------------------------------
        @param self: The object pointer
        @return: send a mail
        """
        now_date = fields.Datetime.now()
        ir_model_data = self.env['ir.model.data']
        template_id = ir_model_data.get_object_reference(
            'hotel_reservation',
            'mail_template_reservation_reminder_24hrs')[1]
        template_rec = self.env['mail.template'].browse(template_id)
        for reserv_rec in self.search([]):
            checkin_date = datetime.strptime(reserv_rec.checkin, DEFAULT_SERVER_DATETIME_FORMAT)
            difference = relativedelta(now_date, checkin_date)
            if(difference.days == -1 and reserv_rec.partner_id.email and
               reserv_rec.state == 'confirm'):
                template_rec.send_mail(reserv_rec.id, force_send=True)
        return True

    @api.multi
    def get_grouped_reservations_json(self, state, import_all=False):
        self.ensure_one()
        info_grouped = []
        for rline in self.room_lines:
            if (import_all or rline.to_send) and \
                    not rline.parent_reservation and rline.state == state:
                dates = (rline.real_checkin, rline.real_checkout)
                vals = {
                    'num': len(
                        self.room_lines.filtered(
                            lambda r: r.real_checkin == dates[0] and \
                            r.real_checkout == dates[1] and \
                            r.room_type_id.id == rline.room_type_id.id and \
                            (r.to_send or import_all) and not r.parent_reservation and \
                            r.state == rline.state)
                    ),
                    'room_type': {
                        'id': rline.room_type_id.id,
                        'name': rline.room_type_id.name,
                    },
                    'checkin': dates[0],
                    'checkout': dates[1],
                    'nights': len(rline.reservation_line_ids),
                    'adults': rline.adults,
                    'childrens': rline.children,
                }
                founded = False
                for srline in info_grouped:
                    if srline['num'] == vals['num'] and \
                        srline['room_type']['id'] == vals['room_type']['id'] and \
                        srline['checkin'] == vals['checkin'] and \
                        srline['checkout'] == vals['checkout']:
                        founded = True
                        break
                if not founded:
                    info_grouped.append(vals)
        return sorted(sorted(info_grouped,key=lambda k: k['num'], reverse=True),
                      key=lambda k: k['room_type']['id'])

    @api.multi
    def _get_tax_amount_by_group(self):
        self.ensure_one()
        res = {}
        for line in self.room_lines:
            price_reduce = line.price_total
            product = line.room_type_id.product_id
            taxes = line.tax_ids.compute_all(price_reduce, quantity=1, product=product)['taxes']
            for tax in line.tax_ids:
                group = tax.tax_group_id
                res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                for t in taxes:
                    if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                        res[group]['amount'] += t['amount']
                        res[group]['base'] += t['base']
        for line in self.service_ids:
            price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
            taxes = line.tax_ids.compute_all(price_reduce, quantity=line.product_qty, product=line.product_id)['taxes']
            for tax in line.tax_ids:
                group = tax.tax_group_id
                res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                for t in taxes:
                    if t['id'] == tax.id or t['id'] in tax.children_tax_ids.ids:
                        res[group]['amount'] += t['amount']
                        res[group]['base'] += t['base']
        res = sorted(res.items(), key=lambda l: l[0].sequence)
        res = [(l[0].name, l[1]['amount'], l[1]['base'], len(res)) for l in res]
        return res
