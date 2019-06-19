# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta


class FolioAdvancePaymentInv(models.TransientModel):
    _name = "folio.advance.payment.inv"
    _description = "Folios Advance Payment Invoice"

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
        if folios[0].tour_operator_id:
            return folios[0].tour_operator_id
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
    auto_invoice = fields.Boolean('Auto Payment Invoice',
                                  default=True,
                                  help='Automatic validation and link payment to invoice')
    count = fields.Integer(compute='_count', store=True, string='# of Orders')
    folio_ids = fields.Many2many("hotel.folio", string="Folios",
                                  help="Folios grouped",
                                  default=_get_default_folio)
    reservation_ids = fields.Many2many("hotel.reservation", string="Rooms",
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

    @api.depends('folio_ids')
    def _count(self):
        for record in self:
            record.update({'count': len(self.folio_ids)})

    @api.onchange('advance_payment_method')
    def onchange_advance_payment_method(self):
        if self.advance_payment_method == 'percentage':
            return {'value': {'amount': 0}}
        return {}

    @api.multi
    def _create_invoice(self, folio, service, amount):
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']

        account_id = False
        if self.product_id.id:
            account_id = self.product_id.property_account_income_id.id \
                or self.product_id.categ_id.property_account_income_categ_id.id
        if not account_id:
            inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
            account_id = folio.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
        if not account_id:
            raise UserError(
                _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                (self.product_id.name,))

        if self.amount <= 0.00:
            raise UserError(_('The value of the down payment amount must be positive.'))
        context = {'lang': folio.partner_id.lang}
        if self.advance_payment_method == 'percentage':
            amount = folio.amount_untaxed * self.amount / 100
            name = _("Down payment of %s%%") % (self.amount,)
        else:
            amount = self.amount
            name = _('Down Payment')
        del context
        taxes = self.product_id.taxes_id.filtered(
            lambda r: not folio.company_id or r.company_id == folio.company_id)
        if folio.fiscal_position_id and taxes:
            tax_ids = folio.fiscal_position_id.map_tax(taxes).ids
        else:
            tax_ids = taxes.ids

        invoice = inv_obj.create({
            'name': folio.client_order_ref or folio.name,
            'origin': folio.name,
            'type': 'out_invoice',
            'reference': False,
            'folio_ids': [(6, 0, [folio.id])],
            'account_id': folio.partner_id.property_account_receivable_id.id,
            'partner_id': folio.partner_invoice_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name,
                'origin': folio.name,
                'account_id': account_id,
                'price_unit': amount,
                'quantity': 1.0,
                'discount': 0.0,
                'uom_id': self.product_id.uom_id.id,
                'product_id': self.product_id.id,
                'service_ids': [(6, 0, [service.id])],
                'invoice_line_tax_ids': [(6, 0, tax_ids)],
                'account_analytic_id': folio.analytic_account_id.id or False,
            })],
            'currency_id': folio.pricelist_id.currency_id.id,
            'payment_term_id': folio.payment_term_id.id,
            'fiscal_position_id': folio.fiscal_position_id.id \
                or folio.partner_id.property_account_position_id.id,
            'team_id': folio.team_id.id,
            'user_id': folio.user_id.id,
            'comment': folio.note,
        })
        invoice.compute_taxes()
        invoice.message_post_with_view(
            'mail.message_origin_link',
            values={'self': invoice, 'origin': folio},
            subtype_id=self.env.ref('mail.mt_note').id)
        return invoice

    @api.model
    def _validate_invoices(self, invoice):
        if self.auto_invoice:
            invoice.action_invoice_open()
            payment_ids = self.folio_ids.mapped('payment_ids.id')
            domain = [
                ('account_id', '=', invoice.account_id.id),
                ('payment_id', 'in', payment_ids),
                ('reconciled', '=', False),
                '|', ('amount_residual', '!=', 0.0),
                ('amount_residual_currency', '!=', 0.0)
                ]
            if invoice.type in ('out_invoice', 'in_refund'):
                domain.extend([('credit', '>', 0), ('debit', '=', 0)])
                type_payment = _('Outstanding credits')
            else:
                domain.extend([('credit', '=', 0), ('debit', '>', 0)])
                type_payment = _('Outstanding debits')
            info = {'title': '', 'outstanding': True, 'content': [], 'invoice_id': invoice.id}
            lines = self.env['account.move.line'].search(domain)
            currency_id = invoice.currency_id
            for line in lines:
                invoice.assign_outstanding_credit(line.id)
        return True

    @api.multi
    def create_invoices(self):
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        folios = self.folio_ids


        if not self.partner_invoice_id or not self.partner_invoice_id.vat:
            vat_error = _("We need the VAT of the customer")
            raise ValidationError(vat_error)

        if self.advance_payment_method == 'all':
            inv_data = self._prepare_invoice()
            invoice = inv_obj.create(inv_data)
            for line in self.line_ids:
                line.invoice_line_create(invoice.id, line.qty)
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].sudo().create(vals)
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
                    'product_qty': 0.0,
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
        self._validate_invoices(invoice)
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
        vals = [(5,0,0)]
        folios = self.folio_ids
        invoice_lines = {}
        for folio in folios:
            for service in folio.service_ids.filtered(
                    lambda x: x.is_board_service == False and \
                    x.qty_to_invoice != 0 and \
                    (x.ser_room_line.id in self.reservation_ids.ids or \
                    not x.ser_room_line.id)):
                invoice_lines[service.id] = {
                    'description': service.name,
                    'product_id': service.product_id.id,
                    'qty': service.qty_to_invoice,
                    'discount': service.discount,
                    'price_unit': service.price_unit,
                    'service_id': service.id,
                    }
            for reservation in folio.room_lines.filtered(
                    lambda x: x.id in self.reservation_ids.ids and
                    x.invoice_status == 'to invoice'):
                board_service = reservation.board_service_room_id
                for day in reservation.reservation_line_ids.filtered(
                        lambda x: not x.invoice_line_ids).sorted('date'):
                    extra_price = 0
                    if board_service:
                        services = reservation.service_ids.filtered(
                            lambda x: x.is_board_service == True)
                        for service in services:
                            service_date = day.date
                            if service.product_id.consumed_on == 'after':
                                service_date = (fields.Date.from_string(day.date) + \
                                    timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
                            extra_price += service.price_unit * \
                                service.service_line_ids.filtered(
                                    lambda x: x.date == service_date).day_qty
                    #group_key: if group by reservation, We no need group by room_type
                    group_key = (reservation.id, reservation.room_type_id.id,
                                 day.price + extra_price, day.discount,
                                 day.cancel_discount)
                    if day.cancel_discount == 100:
                        continue
                    discount_factor = 1.0
                    for discount in [day.discount, day.cancel_discount]:
                        discount_factor = (
                            discount_factor * ((100.0 - discount) / 100.0))
                    final_discount = 100.0 - (discount_factor * 100.0)
                    description = folio.name + ' ' + reservation.room_type_id.name + ' (' + \
                        reservation.board_service_room_id.hotel_board_service_id.name + ')' \
                        if board_service else folio.name + ' ' + reservation.room_type_id.name
                    if group_key not in invoice_lines:
                        invoice_lines[group_key] = {
                            'description': description,
                            'reservation_id': reservation.id,
                            'room_type_id': reservation.room_type_id,
                            'product_id': self.env['product.product'].browse(
                                reservation.room_type_id.product_id.id),
                            'discount': final_discount,
                            'price_unit': day.price + extra_price,
                            'reservation_line_ids': [(4, day.id)]
                        }
                    else:
                        invoice_lines[group_key][('reservation_line_ids')].append((4,day.id))
        for group_key in invoice_lines:
            vals.append((0, False, invoice_lines[group_key]))
        self.line_ids = vals
        self.line_ids.onchange_reservation_line_ids()

    @api.onchange('folio_ids')
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
        # REVIEW: Multi pricelist in folios??
        # for folio in self.folio_ids:
        #     if folio.pricelist_id != pricelist:
        #         raise UserError(_('All Folios must hace the same pricelist'))
        invoice_vals = {
            'name': self.folio_ids[0].client_order_ref or '',
            'origin': origin,
            'type': 'out_invoice',
            'account_id': self.partner_invoice_id.property_account_receivable_id.id,
            'partner_id': self.partner_invoice_id.id,
            'journal_id': journal_id,
            'currency_id': currency.id,
            'payment_term_id': payment_term.id,
            'fiscal_position_id': fiscal_position.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': company.id,
            'user_id': user and user.id,
            'team_id': team.id,
            'comment': self.folio_ids[0].note
        }
        return invoice_vals

class LineAdvancePaymentInv(models.TransientModel):
    _name = "line.advance.inv"
    _description = "Lines Advance Invoice"

    room_type_id = fields.Many2one('hotel.room.type')
    product_id = fields.Many2one('product.product', string='Down Payment Product',
                                 domain=[('type', '=', 'service')])
    qty = fields.Integer('Quantity')
    price_unit = fields.Float('Price Unit')
    price_total = fields.Float('Price Total', compute='_compute_price_total')
    price_tax = fields.Float('Price Tax', compute='_compute_price_total')
    price_subtotal = fields.Float('Price Subtotal',
                                  compute='_compute_price_total',
                                  store=True)
    advance_inv_id = fields.Many2one('folio.advance.payment.inv')
    price_room = fields.Float(compute='_compute_price_room')
    discount = fields.Float(
        string='Discount (%)',
        digits=dp.get_precision('Discount'), default=0.0)
    to_invoice = fields.Boolean('To Invoice')
    description = fields.Text('Description')
    description_dates =  fields.Text('Range')
    reservation_id = fields.Many2one('hotel.reservation')
    service_id = fields.Many2one('hotel.service')
    folio_id = fields.Many2one('hotel.folio', compute='_compute_folio_id')
    reservation_line_ids = fields.Many2many(
        'hotel.reservation.line',
        string='Reservation Lines')

    @api.depends('qty', 'price_unit', 'discount')
    def _compute_price_total(self):
        for record in self:
            origin = record.reservation_id if record.reservation_id.id else record.service_id
            amount_line = record.price_unit * record.qty
            if amount_line != 0:
                product = record.product_id
                price = amount_line * (1 - (record.discount or 0.0) * 0.01)
                taxes = origin.tax_ids.compute_all(price, origin.currency_id, 1, product=product)
                record.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })

    def _compute_price_room(self):
        for record in self:
            if record.reservation_id:
                record.price_room = record.reservation_line_ids[0].price

    def _compute_folio_id(self):
        for record in self:
            origin = record.reservation_id if record.reservation_id.id else record.service_id
            record.folio_id = origin.folio_id

    @api.onchange('reservation_line_ids')
    def onchange_reservation_line_ids(self):
        for record in self:
            if record.reservation_id:
                if not record.reservation_line_ids:
                    raise UserError(_('If you want drop the line, use the trash icon'))
                record.qty = len(record.reservation_line_ids)
                record.description_dates = record.reservation_line_ids[0].date + ' - ' + \
                    ((fields.Date.from_string(record.reservation_line_ids[-1].date)) + \
                        timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)

    @api.multi
    def invoice_line_create(self, invoice_id, qty):
        """ Create an invoice line.
            :param invoice_id: integer
            :param qty: float quantity to invoice
            :returns recordset of account.invoice.line created
        """
        self.ensure_one()
        invoice_lines = self.env['account.invoice.line']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        origin = self.reservation_id if self.reservation_id.id else self.service_id
        product = self.product_id
        account = product.property_account_income_id or product.categ_id.property_account_income_categ_id
        if not account:
            raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (product.name, product.id, product.categ_id.name))

        fpos = self.folio_id.fiscal_position_id or self.folio_id.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)
        vals = {
            'sequence': origin.sequence,
            'origin': origin.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': self.qty,
            'discount': self.discount,
            'uom_id': product.uom_id.id,
            'product_id': product.id or False,
            'invoice_line_tax_ids': [(6, 0, origin.tax_ids.ids)],
            'account_analytic_id': self.folio_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, origin.analytic_tag_ids.ids)]
        }
        if self.reservation_id:
            vals.update({
                'name': self.description + ' (' + self.description_dates + ')',
                'invoice_id': invoice_id,
                'reservation_ids': [(6, 0, [origin.id])],
                'reservation_line_ids': [(6, 0, self.reservation_line_ids.ids)]
            })
        elif self.service_id:
            vals.update({
                'name': self.description,
                'invoice_id': invoice_id,
                'service_ids': [(6, 0, [origin.id])]
            })
        invoice_lines |= self.env['account.invoice.line'].create(vals)
        return invoice_lines
