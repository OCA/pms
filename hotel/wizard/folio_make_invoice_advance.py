# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from datetime import timedelta


class FolioAdvancePaymentInv(models.TransientModel):
    _name = "folio.advance.payment.inv"
    _description = "Folios Advance Payment Invoice"

    @api.model
    def _count(self):
        return len(self._context.get('active_ids', []))

    @api.model
    def _get_advance_payment_method(self):
        return 'all'

    @api.model
    def _default_product_id(self):
        product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
        return self.env['product.product'].browse(int(product_id))

    @api.model
    def _get_default_folio(self):
        if self._context.get('default_reservation_id'):
            folio_ids = self._context.get('default_folio_id', [])
        else:
            folio_ids = self._context.get('active_ids', [])
        
        folios = self.env['hotel.folio'].browse(folio_ids)
        return folios

    @api.model
    def _get_default_reservation(self):
        if self._context.get('default_reservation_id'):
            reservations = self.env['hotel.reservation'].browse(self._context.get('active_ids', []))
        else:
            folios = self._get_default_folio()
            reservations = self.env['hotel.reservation']
            for folio in folios:
                reservations |= folio.room_lines
        return reservations

    @api.model
    def _get_default_partner_invoice(self):
        folios = self._get_default_folio()
        return folios[0].partner_invoice_id

    @api.model
    def _default_deposit_account_id(self):
        return self._default_product_id().property_account_income_id

    @api.model
    def _default_deposit_taxes_id(self):
        return self._default_product_id().taxes_id

    advance_payment_method = fields.Selection([
        ('all', 'Invoiceable lines (deduct down payments)'),
        ('percentage', 'Down payment (percentage)'),
        ('fixed', 'Down payment (fixed amount)')
    ], string='What do you want to invoice?', default=_get_advance_payment_method,
                                              required=True)
    count = fields.Integer(default=_count, string='# of Orders')
    folio_ids  = fields.Many2many("hotel.folio", string="Folios",
                                  help="Folios grouped",
                                  default=_get_default_folio)
    reservation_ids  = fields.Many2many("hotel.reservation", string="Rooms",
                                  help="Folios grouped",
                                  default=_get_default_reservation)
    group_folios = fields.Boolean('Group Folios')
    partner_invoice_id = fields.Many2one('res.partner',
                                         string='Invoice Address', required=True,
                                         default=_get_default_partner_invoice,
                                         help="Invoice address for current Invoice.")
    line_ids = fields.One2many('line.advance.inv',
                               'advance_inv_id',
                               string="Invoice Lines")
    view_detail = fields.Boolean('View Detail')
    #Advance Payment
    product_id = fields.Many2one('product.product', string="Product",
                                 domain=[('type', '=', 'service')], default=_default_product_id)
    amount = fields.Float('Down Payment Amount',
                          digits=dp.get_precision('Account'),
                          help="The amount to be invoiced in advance, taxes excluded.")
    deposit_account_id = fields.Many2one("account.account", string="Income Account",
                                         domain=[('deprecated', '=', False)],
                                         help="Account used for deposits",
                                         default=_default_deposit_account_id)
    deposit_taxes_id = fields.Many2many("account.tax", string="Customer Taxes",
                                        help="Taxes used for deposits",
                                        default=_default_deposit_taxes_id)

    @api.onchange('advance_payment_method')
    def onchange_advance_payment_method(self):
        if self.advance_payment_method == 'percentage':
            return {'value': {'amount': 0}}
        return {}

    @api.multi
    def _create_invoice(self, order, so_line, amount):
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']

        account_id = False
        if self.product_id.id:
            account_id = self.product_id.property_account_income_id.id \
                or self.product_id.categ_id.property_account_income_categ_id.id
        if not account_id:
            inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            account_id = order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
        if not account_id:
            raise UserError(
                _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                (self.product_id.name,))

        if self.amount <= 0.00:
            raise UserError(_('The value of the down payment amount must be positive.'))
        context = {'lang': order.partner_id.lang}
        if self.advance_payment_method == 'percentage':
            amount = order.amount_untaxed * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount,)
        else:
            amount = self.amount
            name = _('Down Payment')
        del context
        taxes = self.product_id.taxes_id.filtered(
            lambda r: not order.company_id or r.company_id == order.company_id)
        if order.fiscal_position_id and taxes:
            tax_ids = order.fiscal_position_id.map_tax(taxes).ids
        else:
            tax_ids = taxes.ids

        invoice = inv_obj.create({
            'name': order.client_order_ref or order.name,
            'origin': order.name,
            'type': 'out_invoice',
            'reference': False,
            'account_id': order.partner_id.property_account_receivable_id.id,
            'partner_id': order.partner_invoice_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'origin': order.name,
                'account_id': account_id,
                'price_unit': amount,
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': self.product_id.uom_id.id,
                'product_id': self.product_id.id,
                'sale_line_ids': [(6, 0, [so_line.id])],
                'invoice_line_tax_ids': [(6, 0, tax_ids)],
                'account_analytic_id': order.analytic_account_id.id or False,
            })],
            'currency_id': order.pricelist_id.currency_id.id,
            'payment_term_id': order.payment_term_id.id,
            'fiscal_position_id': order.fiscal_position_id.id \
                or order.partner_id.property_account_position_id.id,
            'team_id': order.team_id.id,
            'user_id': order.user_id.id,
            'comment': order.note,
        })
        invoice.compute_taxes()
        invoice.message_post_with_view(
            'mail.message_origin_link',
            values={'self': invoice, 'origin': order},
            subtype_id=self.env.ref('mail.mt_note').id)
        return invoice

    @api.multi
    def create_invoices(self):
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        folios = self.folio_ids

        for folio in folios:
            if folio.partner_invoice_id != self.partner_invoice_id:
                raise UserError(_('The billing directions must match'))
                            
        if self.advance_payment_method == 'all':
            inv_data = self._prepare_invoice()
            invoice = inv_obj.create(inv_data)
            for line in self.line_ids:
                line.invoice_line_create(invoice.id, line.qty)
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.config_parameter'].sudo().set_param(
                    'sale.default_deposit_product_id', self.product_id.id)

            service_obj = self.env['hotel.service']
            for folio in folios:
                if self.advance_payment_method == 'percentage':
                    amount = folio.amount_untaxed * folio.amount_total / 100
                else:
                    amount = self.amount
                if self.product_id.invoice_policy != 'order':
                    raise UserError(_('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(_("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                taxes = self.product_id.taxes_id.filtered(
                    lambda r: not folio.company_id or r.company_id == folio.company_id)
                if folio.fiscal_position_id and taxes:
                    tax_ids = folio.fiscal_position_id.map_tax(taxes).ids
                else:
                    tax_ids = taxes.ids
                context = {'lang': folio.partner_id.lang}
                service_line = service_obj.create({
                    'name': _('Advance: %s') % (time.strftime('%m %Y'),),
                    'price_unit': amount,
                    'product_uom_qty': 0.0,
                    'folio_id': folio.id,
                    'discount': 0.0,
                    'product_uom': self.product_id.uom_id.id,
                    'product_id': self.product_id.id,
                    'tax_id': [(6, 0, tax_ids)],
                })
                del context
                invoice = self._create_invoice(folio, service_line, amount)
        invoice.compute_taxes()
        if not invoice.invoice_line_ids:
            raise UserError(_('There is no invoiceable line.'))
        # If invoice is negative, do a refund invoice instead
        if invoice.amount_total < 0:
            invoice.type = 'out_refund'
            for line in invoice.invoice_line_ids:
                line.quantity = -line.quantity
        # Use additional field helper function (for account extensions)
        for line in invoice.invoice_line_ids:
            line._set_additional_fields(invoice)
        # Necessary to force computation of taxes. In account_invoice, they are triggered
        # by onchanges, which are not triggered when doing a create.
        invoice.compute_taxes()
        invoice.message_post_with_view('mail.message_origin_link',
            values={'self': invoice, 'origin': folios},
            subtype_id=self.env.ref('mail.mt_note').id)
        if self._context.get('open_invoices', False):
            return folios.open_invoices_folio()
        return {'type': 'ir.actions.act_window_close'}

    def _prepare_deposit_product(self):
        return {
            'name': 'Down payment',
            'type': 'service',
            'invoice_policy': 'order',
            'property_account_income_id': self.deposit_account_id.id,
            'taxes_id': [(6, 0, self.deposit_taxes_id.ids)],
        }

    @api.onchange('reservation_ids')
    def prepare_invoice_lines(self):
        vals = []
        folios = self.folio_ids
        invoice_lines = {}
        for folio in folios:
            for service in folio.service_ids.filtered(
                    lambda x: x.is_board_service == False and \
                    (x.ser_room_line.id in self.reservation_ids.ids or \
                    x.ser_room_line.id  == False)):
                invoice_lines[service.id] = {
                        'description' : service.name,
                        'product_id': service.product_id.id,
                        'qty': service.product_qty,
                        'discount': service.discount,
                        'price_unit': service.price_unit,
                        'service_id': service.id,
                        }               
            for reservation in folio.room_lines.filtered(
                    lambda x: x.id in self.reservation_ids.ids):
                board_service = reservation.board_service_room_id
                for day in reservation.reservation_line_ids.sorted('date'):
                    extra_price = 0
                    if board_service:
                        services = reservation.service_ids.filtered(
                            lambda x: x.is_board_service == True)
                        for service in services:
                            extra_price += service.price_unit * \
                                service.service_line_ids.filtered(
                                    lambda x: x.date == day.date).day_qty                            
                    group_key = (reservation.id, reservation.room_type_id.id, day.price + extra_price, day.discount)
                    date = fields.Date.from_string(day.date)
                    if group_key in invoice_lines:                     
                        invoice_lines[group_key][('qty')] += 1
                        if date == fields.Date.from_string(
                                    invoice_lines[group_key][('date_to')]) + timedelta(days=1):
                            desc = invoice_lines[group_key][('description')]                        
                            invoice_lines[group_key][('description')] = \
                                desc.replace(desc[desc.rfind(" - "):], ' - ' + \
                                    (date + timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT) + ')')
                        else:
                            invoice_lines[group_key][('description')] += \
                                ' (' + date.strftime(DEFAULT_SERVER_DATE_FORMAT) + \
                                ' - ' + (date + timedelta(days=1)).strftime(
                                DEFAULT_SERVER_DATE_FORMAT) + \
                                ')'
                        invoice_lines[group_key][('date_to')] = day.date
                    else:
                        room_type_description = folio.name + ' ' + reservation.room_type_id.name + ' (' + \
                            reservation.board_service_room_id.hotel_board_service_id.name + ')' \
                            if board_service else folio.name + ' ' + reservation.room_type_id.name
                        description = room_type_description + \
                            ': (' + date.strftime(DEFAULT_SERVER_DATE_FORMAT) + \
                            ' - ' + (date + timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT) + \
                            ')'
                        invoice_lines[group_key] = {
                        'description' : description,
                        'reservation_id': reservation.id,
                        'room_type_id': reservation.room_type_id,
                        'product_id': self.env['product.product'].browse(
                            reservation.room_type_id.product_id.id
                            ),
                        'qty': 1,
                        'discount': day.discount,
                        'price_unit': day.price + extra_price,
                        'date_to': day.date,
                        'reservation_line_ids': []
                        }
                    invoice_lines[group_key][('reservation_line_ids')].append((4,day.id))
        for group_key in invoice_lines:
            vals.append((0, False, invoice_lines[group_key]))
        self.line_ids = vals

    @api.onchange('view_detail', 'folio_ids')
    def onchange_folio_ids(self):
        vals = []
        folios = self.folio_ids
        invoice_lines = {}
        reservations = self.env['hotel.reservation']
        services = self.env['hotel.service']
        old_folio_ids = self.reservation_ids.mapped('folio_id.id')
        for folio in folios.filtered(lambda r: r.id not in old_folio_ids):
            folio_reservations = folio.room_lines
            if folio_reservations:
                reservations |= folio_reservations
        self.reservation_ids |= reservations
        self.prepare_invoice_lines()

    @api.model
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a folio. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
    
        journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting sales journal for this company.'))
        origin = ' '.join(self.folio_ids.mapped('name'))
        pricelist = self.folio_ids[0].pricelist_id
        currency = self.folio_ids[0].currency_id
        payment_term = self.folio_ids[0].payment_term_id
        fiscal_position = self.folio_ids[0].fiscal_position_id
        company = self.folio_ids[0].company_id
        user = self.folio_ids[0].user_id
        team = self.folio_ids[0].team_id
        for folio in self.folio_ids:
            if folio.pricelist_id != pricelist:
                raise UserError(_('All Folios must hace the same pricelist'))
        invoice_vals = {
            'name': self.folio_ids[0].client_order_ref or '',
            'origin': origin,
            'type': 'out_invoice',
            'account_id': self.partner_invoice_id.property_account_receivable_id.id,
            'partner_id': self.partner_invoice_id.id,
            'journal_id': journal_id,
            'currency_id': pricelist.id,
            'payment_term_id': payment_term.id,
            'fiscal_position_id': fiscal_position.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': company.id,
            'user_id': user and user.id,
            'team_id': team.id
        }
        return invoice_vals

class LineAdvancePaymentInv(models.TransientModel):
    _name = "line.advance.inv"
    _description = "Lines Advance Invoice"

    room_type_id = fields.Many2one('hotel.room.type')
    product_id = fields.Many2one('product.product', string='Down Payment Product',
                                 domain=[('type', '=', 'service')])
    qty = fields.Integer('Quantity')
    price_unit = fields.Float('Price')
    advance_inv_id = fields.Many2one('folio.advance.payment.inv')
    discount = fields.Float(
        string='Discount (%)',
        digits=dp.get_precision('Discount'), default=0.0)
    to_invoice = fields.Boolean('To Invoice')
    description = fields.Text('Description')
    reservation_id = fields.Many2one('hotel.reservation')
    service_id = fields.Many2one('hotel.service')
    folio_id = fields.Many2one('hotel.folio', compute='_compute_folio_id')
    reservation_line_ids = fields.Many2many(
        'hotel.reservation.line',
        string='Reservation Lines')

    def _compute_folio_id(self):
        for record in self:
            origin = record.reservation_id if record.reservation_id.id else record.service_id
            record.folio_id = origin.folio_id
                    
    @api.multi
    def invoice_line_create(self, invoice_id, qty):
        """ Create an invoice line.
            :param invoice_id: integer
            :param qty: float quantity to invoice
            :returns recordset of account.invoice.line created
        """
        invoice_lines = self.env['account.invoice.line']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            origin = line.reservation_id if line.reservation_id.id else line.service_id
            res = {}
            product = line.product_id
            account = product.property_account_income_id or product.categ_id.property_account_income_categ_id
            if not account:
                raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                    (product.name, product.id, product.categ_id.name))

            fpos = line.folio_id.fiscal_position_id or line.folio_id.partner_id.property_account_position_id
            if fpos:
                account = fpos.map_account(account)
            vals = {
                'name': line.description,
                'sequence': origin.sequence,
                'origin': origin.name,
                'account_id': account.id,
                'price_unit': line.price_unit,
                'quantity': line.qty,
                'discount': line.discount,
                'uom_id': product.uom_id.id,
                'product_id': product.id or False,
                'invoice_line_tax_ids': [(6, 0, origin.tax_ids.ids)],
                'account_analytic_id': line.folio_id.analytic_account_id.id,
                'analytic_tag_ids': [(6, 0, origin.analytic_tag_ids.ids)]
            }
            if line.reservation_id:
                vals.update({
                    'invoice_id': invoice_id,
                    'reservation_ids': [(6, 0, [origin.id])],
                    'reservation_line_ids': [(6, 0, line.reservation_line_ids.ids)]
                })
            elif line.service_id:
                vals.update({
                    'invoice_id': invoice_id,
                    'service_ids': [(6, 0, [origin.id])]
                })
            invoice_lines |= self.env['account.invoice.line'].create(vals)
                
        return invoice_lines
