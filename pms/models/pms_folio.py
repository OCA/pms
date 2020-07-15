# Copyright 2017-2018  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class PmsFolio(models.Model):
    _name = 'pms.folio'
    _description = 'PMS Folio'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'id'

    # Default Methods ang Gets
    @api.model
    def _default_diff_invoicing(self):
        """
        If the guest has an invoicing address set,
        this method return diff_invoicing = True, else, return False
        """
        if 'folio_id' in self.env.context:
            folio = self.env['pms.folio'].browse([
                self.env.context['folio_id']
            ])
        if folio.partner_id.id == folio.partner_invoice_id.id:
            return False
        return True

    @api.model
    def _get_default_team(self):
        return self.env['crm.team']._get_default_team_id()

    @api.model
    def _get_default_pms_property(self):
        return self.env.user.pms_property_id

    # Fields declaration
    name = fields.Char(
        String='Folio Number',
        readonly=True,
        index=True,
        default=lambda self: _('New'))
    pms_property_id = fields.Many2one(
        'pms.property',
        default=_get_default_pms_property,
        required=True)
    partner_id = fields.Many2one(
        'res.partner',
        track_visibility='onchange',
        ondelete='restrict')
    reservation_ids = fields.One2many(
        'pms.reservation',
        'folio_id',
        readonly=False,
        states={'done': [('readonly', True)]},
        help="Room reservation detail.",)
    service_ids = fields.One2many(
        'pms.service',
        'folio_id',
        readonly=False,
        states={'done': [('readonly', True)]},
        help="Services detail provide to customer and it will "
        "include in main Invoice.")
    company_id = fields.Many2one(
        'res.company',
        'Company',
        default=lambda self: self.env.company)
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        'Analytic Account',
        readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        help="The analytic account related to a folio.",
        copy=False)
    currency_id = fields.Many2one(
        'res.currency',
        related='pricelist_id.currency_id',
        string='Currency',
        readonly=True,
        required=True,
        ondelete='restrict',)
    pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Pricelist',
        required=True,
        ondelete='restrict',
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        help="Pricelist for current folio.")
    user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        index=True,
        ondelete='restrict',
        track_visibility='onchange',
        default=lambda self: self.env.user)
    tour_operator_id = fields.Many2one(
        'res.partner',
        'Tour Operator',
        ondelete='restrict',
        domain=[('is_tour_operator', '=', True)])
    payment_ids = fields.One2many(
        'account.payment',
        'folio_id',
        readonly=True)
    return_ids = fields.One2many(
        'payment.return',
        'folio_id',
        readonly=True)
    payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Payment Terms')
    checkin_partner_ids = fields.One2many(
        'pms.checkin.partner',
        'folio_id')
    move_ids = fields.Many2many(
        'account.move',
        string='Invoices',
        compute='_get_invoiced',
        readonly=True,
        copy=False)
    partner_invoice_id = fields.Many2one(
        'res.partner',
        string='Invoice Address',
        required=True,
        states={'done': [('readonly', True)]},
        help="Invoice address for current sales order.")
    partner_parent_id = fields.Many2one(
        related="partner_id.parent_id")
    partner_invoice_state_id = fields.Many2one(
        related="partner_invoice_id.state_id")
    partner_invoice_country_id = fields.Many2one(
        related="partner_invoice_id.country_id")
    fiscal_position_id = fields.Many2one(
        'account.fiscal.position',
        string='Fiscal Position')
    closure_reason_id = fields.Many2one(
        'room.closure.reason')
    segmentation_ids = fields.Many2many(
        'res.partner.category',
        string='Segmentation',
        ondelete='restrict')
    team_id = fields.Many2one(
        'crm.team',
        string='Sales Team',
        ondelete='restrict',
        change_default=True,
        default=_get_default_team)
    client_order_ref = fields.Char(string='Customer Reference', copy=False)
    reservation_type = fields.Selection([
        ('normal', 'Normal'),
        ('staff', 'Staff'),
        ('out', 'Out of Service')],
        string='Type',
        default=lambda *a: 'normal')
    channel_type = fields.Selection([
        ('door', 'Door'),
        ('mail', 'Mail'),
        ('phone', 'Phone'),
        ('call', 'Call Center'),
        ('web', 'Web'),
        ('agency', 'Agencia'),
        ('operator', 'Tour operador'),
        ('virtualdoor', 'Virtual Door'), ], 'Sales Channel', default='door')
    date_order = fields.Datetime(
        string='Order Date',
        required=True,
        readonly=True,
        index=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        copy=False,
        default=fields.Datetime.now)
    confirmation_date = fields.Datetime(
        string='Confirmation Date',
        readonly=True,
        index=True,
        help="Date on which the folio is confirmed.",
        copy=False)
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('confirm', 'Confirmed'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'), ],
        string='Status',
        readonly=True,
        copy=False,
        index=True,
        track_visibility='onchange',
        default='draft')
    # Partner fields for being used directly in the Folio views---------
    email = fields.Char('E-mail', related='partner_id.email')
    mobile = fields.Char('Mobile', related='partner_id.mobile')
    phone = fields.Char('Phone', related='partner_id.phone')
    partner_internal_comment = fields.Text(string='Internal Partner Notes',
                                           related='partner_id.comment')
    # Payment Fields-----------------------------------------------------
    credit_card_details = fields.Text('Credit Card Details')

    # Amount Fields------------------------------------------------------
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
    amount_total = fields.Monetary(string='Total', store=True,
                                   readonly=True, compute='_amount_all',
                                   track_visibility='always')
    # Checkin Fields-----------------------------------------------------
    booking_pending = fields.Integer(
        'Booking pending', compute='_compute_checkin_partner_count')
    checkin_partner_count = fields.Integer(
        'Checkin counter', compute='_compute_checkin_partner_count')
    checkin_partner_pending_count = fields.Integer(
        'Checkin Pending', compute='_compute_checkin_partner_count')
    # Invoice Fields-----------------------------------------------------
    invoice_count = fields.Integer(compute='_get_invoiced')
    invoice_status = fields.Selection([
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')],
        string='Invoice Status',
        compute='_get_invoiced',
        store=True,
        readonly=True,
        default='no')
    partner_invoice_vat = fields.Char(related="partner_invoice_id.vat")
    partner_invoice_name = fields.Char(related="partner_invoice_id.name", string="Partner Name")
    partner_invoice_street = fields.Char(related="partner_invoice_id.street", string="Street")
    partner_invoice_street2 = fields.Char(related="partner_invoice_id.street", string="Street2")
    partner_invoice_zip = fields.Char(related="partner_invoice_id.zip")
    partner_invoice_city = fields.Char(related="partner_invoice_id.city")
    partner_invoice_email = fields.Char(related="partner_invoice_id.email")
    partner_invoice_lang = fields.Selection(related="partner_invoice_id.lang")
    # WorkFlow Mail Fields-----------------------------------------------
    has_confirmed_reservations_to_send = fields.Boolean(
        compute='_compute_has_confirmed_reservations_to_send')
    has_cancelled_reservations_to_send = fields.Boolean(
        compute='_compute_has_cancelled_reservations_to_send')
    has_checkout_to_send = fields.Boolean(
        compute='_compute_has_checkout_to_send')
    # Generic Fields-----------------------------------------------------
    internal_comment = fields.Text(string='Internal Folio Notes')
    cancelled_reason = fields.Text('Cause of cancelled')
    prepaid_warning_days = fields.Integer(
        'Prepaid Warning Days',
        help='Margin in days to create a notice if a payment \
                advance has not been recorded')
    note = fields.Text('Terms and conditions')
    sequence = fields.Integer(string='Sequence', default=10)

    # Compute and Search methods
    @api.depends('state', 'reservation_ids.invoice_status',
                 'service_ids.invoice_status')
    def _get_invoiced(self):
        """
        Compute the invoice status of a Folio. Possible statuses:
        - no: if the Folio is not in status 'sale' or 'done', we
          consider that there is nothing to invoice.
          This is also the default value if the conditions of no other
          status is met.
        - to invoice: if any Folio line is 'to invoice',
          the whole Folio is 'to invoice'
        - invoiced: if all Folio lines are invoiced, the Folio is invoiced.

        The invoice_ids are obtained thanks to the invoice lines of the
        Folio lines, and we also search for possible refunds created
        directly from existing invoices. This is necessary since such a
        refund is not directly linked to the Folio.
        """
        for folio in self:
            move_ids = folio.reservation_ids.mapped('move_line_ids').\
                mapped('move_id').filtered(lambda r: r.type in [
                    'out_invoice', 'out_refund'])
            invoice_ids = folio.service_ids.mapped('move_line_ids').mapped(
                'move_id').filtered(lambda r: r.type in [
                    'out_invoice', 'out_refund'])
            # TODO: Search for invoices which have been 'cancelled'
            # (filter_refund = 'modify' in 'account.move.refund')
            # use like as origin may contains multiple references
            # (e.g. 'SO01, SO02')
            refunds = invoice_ids.search([
                ('invoice_origin', 'like', folio.name),
                ('company_id', '=', folio.company_id.id)]).filtered(
                    lambda r: r.type in ['out_invoice', 'out_refund'])
            invoice_ids |= refunds.filtered(
                lambda r: folio.id in r.folio_ids.ids)
            # Search for refunds as well
            refund_ids = self.env['account.move'].browse()
            if invoice_ids:
                for inv in invoice_ids:
                    refund_ids += refund_ids.search([
                        ('type', '=', 'out_refund'),
                        ('invoice_origin', '=', inv.number),
                        ('invoice_origin', '!=', False),
                        ('journal_id', '=', inv.journal_id.id)])
            # Ignore the status of the deposit product
            deposit_product_id = self.env['sale.advance.payment.inv'].\
                _default_product_id()
            service_invoice_status = [
                service.invoice_status for service in folio.service_ids
                if service.product_id != deposit_product_id]
            reservation_invoice_status = [
                reservation.invoice_status for reservation in
                folio.reservation_ids]

            if folio.state not in ('confirm', 'done'):
                invoice_status = 'no'
            elif any(invoice_status == 'to invoice' for
                     invoice_status in service_invoice_status) or \
                    any(invoice_status == 'to invoice' for invoice_status
                        in reservation_invoice_status):
                invoice_status = 'to invoice'
            elif all(invoice_status == 'invoiced' for invoice_status in
                     service_invoice_status) or \
                    any(invoice_status == 'invoiced' for invoice_status in
                        reservation_invoice_status):
                invoice_status = 'invoiced'
            else:
                invoice_status = 'no'

            folio.update({
                'invoice_count': len(set(move_ids.ids + refund_ids.ids)),
                'move_ids': move_ids.ids + refund_ids.ids,
                'invoice_status': invoice_status
            })

    @api.depends('reservation_ids.price_total', 'service_ids.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for record in self:
            amount_untaxed = amount_tax = 0.0
            amount_untaxed = \
                sum(record.reservation_ids.mapped('price_subtotal')) + \
                sum(record.service_ids.mapped('price_subtotal'))
            amount_tax = sum(record.reservation_ids.mapped('price_tax')) + \
                sum(record.service_ids.mapped('price_tax'))
            record.update({
                'amount_untaxed': record.pricelist_id.currency_id.round(
                    amount_untaxed),
                'amount_tax': record.pricelist_id.currency_id.round(
                    amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.depends('amount_total', 'payment_ids', 'return_ids',
                 'reservation_type', 'state')

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
                    ('move_line_ids', 'in', payments.mapped(
                        'move_line_ids.id')),
                    ('return_id.state', '=', 'done')
                ])
                total_inv_refund = sum(
                    pay_return.amount for pay_return in return_lines)
                total = record.amount_total
                # REVIEW: Must We ignored services in cancelled folios
                # pending amount?
                if record.state == 'cancelled':
                    total = total - \
                        sum(record.service_ids.mapped('price_total'))
                vals = {
                    'pending_amount': total - total_paid + total_inv_refund,
                    'invoices_paid': total_paid,
                    'refund_amount': total_inv_refund,
                }
                record.update(vals)

    @api.depends('reservation_ids')
    def _compute_has_confirmed_reservations_to_send(self):
        has_to_send = False
        if self.reservation_type != 'out':
            for rline in self.reservation_ids:
                if rline.splitted:
                    master_reservation = rline.parent_reservation or rline
                    has_to_send = self.env['pms.reservation'].search_count([
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

    @api.depends('reservation_ids')
    def _compute_has_cancelled_reservations_to_send(self):
        has_to_send = False
        if self.reservation_type != 'out':
            for rline in self.reservation_ids:
                if rline.splitted:
                    master_reservation = rline.parent_reservation or rline
                    has_to_send = self.env['pms.reservation'].search_count([
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

    @api.depends('reservation_ids')
    def _compute_has_checkout_to_send(self):
        has_to_send = True
        if self.reservation_type != 'out':
            for rline in self.reservation_ids:
                if rline.splitted:
                    master_reservation = rline.parent_reservation or rline
                    nreservs = self.env['pms.reservation'].search_count([
                        ('splitted', '=', True),
                        ('folio_id', '=', self.id),
                        ('to_send', '=', True),
                        ('state', '=', 'done'),
                        '|',
                        ('parent_reservation', '=', master_reservation.id),
                        ('id', '=', master_reservation.id),
                    ])
                    if nreservs != len(self.reservation_ids):
                        has_to_send = False
                elif not rline.to_send or rline.state != 'done':
                    has_to_send = False
                    break
            self.has_checkout_to_send = has_to_send
        else:
            self.has_checkout_to_send = False

    # Constraints and onchanges

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
                'partner_move_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
            })
            return

        addr = self.partner_id.address_get(['invoice'])
        pricelist = self.partner_id.property_product_pricelist and \
            self.partner_id.property_product_pricelist.id or \
            self.env.user.pms_property_id.default_pricelist_id.id
        values = {
            'pricelist_id': pricelist,
            'payment_term_id': self.partner_id.property_payment_term_id and
            self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'user_id': self.partner_id.user_id.id or self.env.uid,
        }

        if self.env['ir.config_parameter'].sudo().\
                get_param('sale.use_sale_note') and \
                self.env.user.company_id.sale_note:
            values['note'] = self.with_context(
                lang=self.partner_id.lang).env.user.company_id.sale_note

        if self.partner_id.team_id:
            values['team_id'] = self.partner_id.team_id.id
        self.update(values)


    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self):
        values = {'reservation_type': self.env['pms.folio'].
                  calcule_reservation_type(
                      self.pricelist_id.is_staff,
                      self.reservation_type
        )}
        self.update(values)

    # Action methods

    def action_pay(self):
        self.ensure_one()
        partner = self.partner_id.id
        amount = self.pending_amount
        view_id = self.env.ref('pms.account_payment_view_form_folio').id
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


    def open_moves_folio(self):
        invoices = self.mapped('move_ids')
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [
                (self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action


    def action_return_payments(self):
        self.ensure_one()
        return_move_ids = []
        acc_pay_obj = self.env['account.payment']
        payments = acc_pay_obj.search([
            '|',
            ('move_ids', 'in', self.move_ids.ids),
            ('folio_id', '=', self.id)
        ])
        return_move_ids += self.move_ids.filtered(
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


    def action_checks(self):
        self.ensure_one()
        rooms = self.mapped('reservation_ids.id')
        return {
            'name': _('Checkins'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'pms.checkin.partner',
            'type': 'ir.actions.act_window',
            'domain': [('reservation_id', 'in', rooms)],
            'target': 'new',
        }


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
                'pms',
                'email_template_reservation')[1]
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
            'default_model': 'pms.folio',
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
                'pms',
                'mail_template_pms_exit')[1]
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
            'default_model': 'pms.reservation',
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


    def send_cancel_mail(self):
        '''
        This function opens a window to compose an email,
        template message loaded by default.
        @param self: object pointer
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference(
                'pms',
                'mail_template_pms_cancel')[1]
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
            'default_model': 'pms.reservation',
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

    # ORM Overrides
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New') or 'name' not in vals:
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(
                    force_company=vals['company_id']
                ).next_by_code('pms.folio') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'pms.folio') or _('New')
        vals.update(self._prepare_add_missing_fields(vals))
        result = super(PmsFolio, self).create(vals)
        return result

    # Business methods
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
                    res[field] = line._fields[field].convert_to_write(
                        line[field], line)
        return res

    @api.model
    def calcule_reservation_type(self, is_staff, current_type):
        if current_type == 'out':
            return 'out'
        elif is_staff:
            return 'staff'
        else:
            return 'normal'


    def action_done(self):
        reservation_ids = self.mapped('reservation_ids')
        for line in reservation_ids:
            if line.state == "booking":
                line.action_reservation_checkout()


    def action_cancel(self):
        for folio in self:
            for reservation in folio.reservation_ids.filtered(
                    lambda res: res.state != 'cancelled'):
                reservation.action_cancel()
            self.write({
                'state': 'cancel',
            })
        return True


    def action_confirm(self):
        for folio in self.filtered(lambda folio: folio.partner_id not in
                                   folio.message_partner_ids):
            folio.message_subscribe([folio.partner_id.id])
        self.write({
            'state': 'confirm',
            'confirmation_date': fields.Datetime.now()
        })
        # if self.env.context.get('send_email'):
        # self.force_quotation_send()

        # create an analytic account if at least an expense product
        # if any([expense_policy != 'no' for expense_policy in
        # self.order_line.mapped('product_id.expense_policy')]):
        # if not self.analytic_account_id:
        # self._create_analytic_account()
        return True

    """
    CHECKIN/OUT PROCESS
    """


    def _compute_checkin_partner_count(self):
        for record in self:
            if record.reservation_type == 'normal' and record.reservation_ids:
                filtered_reservs = record.reservation_ids.filtered(
                    lambda x: x.state != 'cancelled' and
                    not x.parent_reservation)
                mapped_checkin_partner = filtered_reservs.mapped(
                    'checkin_partner_ids.id')
                record.checkin_partner_count = len(mapped_checkin_partner)
                mapped_checkin_partner_count = filtered_reservs.mapped(
                    lambda x: (x.adults + x.children) -
                    len(x.checkin_partner_ids))
                record.checkin_partner_pending_count = sum(
                    mapped_checkin_partner_count)


    def get_grouped_reservations_json(self, state, import_all=False):
        self.ensure_one()
        info_grouped = []
        for rline in self.reservation_ids:
            if (import_all or rline.to_send) and \
                    not rline.parent_reservation and rline.state == state:
                dates = (rline.real_checkin, rline.real_checkout)
                vals = {
                    'num': len(
                        self.reservation_ids.filtered(
                            lambda r: r.real_checkin == dates[0] and
                            r.real_checkout == dates[1] and
                            r.room_type_id.id == rline.room_type_id.id and
                            (r.to_send or import_all) and
                            not r.parent_reservation and
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
                            srline['room_type']['id'] == \
                            vals['room_type']['id'] and \
                            srline['checkin'] == vals['checkin'] and \
                            srline['checkout'] == vals['checkout']:
                        founded = True
                        break
                if not founded:
                    info_grouped.append(vals)
        return sorted(sorted(info_grouped, key=lambda k: k['num'],
                             reverse=True),
                      key=lambda k: k['room_type']['id'])


    def _get_tax_amount_by_group(self):
        self.ensure_one()
        res = {}
        for line in self.reservation_ids:
            price_reduce = line.price_total
            product = line.room_type_id.product_id
            taxes = line.tax_ids.compute_all(
                price_reduce, quantity=1, product=product)['taxes']
            for tax in line.tax_ids:
                group = tax.tax_group_id
                res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                for t in taxes:
                    if t['id'] == tax.id or t['id'] in \
                            tax.children_tax_ids.ids:
                        res[group]['amount'] += t['amount']
                        res[group]['base'] += t['base']
        for line in self.service_ids:
            price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
            taxes = line.tax_ids.compute_all(
                price_reduce, quantity=line.product_qty,
                product=line.product_id)['taxes']
            for tax in line.tax_ids:
                group = tax.tax_group_id
                res.setdefault(group, {'amount': 0.0, 'base': 0.0})
                for t in taxes:
                    if t['id'] == tax.id or t['id'] in \
                            tax.children_tax_ids.ids:
                        res[group]['amount'] += t['amount']
                        res[group]['base'] += t['base']
        res = sorted(res.items(), key=lambda l: l[0].sequence)
        res = [(l[0].name, l[1]['amount'], l[1]['base'], len(res))
               for l in res]
        return res
