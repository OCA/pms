# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.tools import (
    float_is_zero,
    float_compare,
    DEFAULT_SERVER_DATE_FORMAT)
from datetime import timedelta
from odoo.addons import decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)


class PmsService(models.Model):
    _name = 'pms.service'
    _description = 'Services and its charges'

    # Default methods
    
    def name_get(self):
        result = []
        for rec in self:
            name = []
            name.append('%(name)s' % {'name': rec.name})
            if rec.reservation_id.name:
                name.append('%(name)s' % {'name': rec.reservation_id.name})
            result.append((rec.id, ", ".join(name)))
        return result

    @api.model
    def _default_reservation_id(self):
        if self.env.context.get('reservation_ids'):
            ids = [item[1] for item in self.env.context['reservation_ids']]
            return self.env['pms.reservation'].browse([
                (ids)], limit=1)
        elif self.env.context.get('default_reservation_id'):
            return self.env.context.get('default_reservation_id')
        return False

    @api.model
    def _default_folio_id(self):
        if 'folio_id' in self._context:
            return self._context['folio_id']
        return False

    # Fields declaration
    name = fields.Char('Service description', required=True)
    product_id = fields.Many2one(
        'product.product',
        'Service',
        ondelete='restrict',
        required=True)
    folio_id = fields.Many2one(
        'pms.folio',
        'Folio',
        ondelete='cascade',
        default=_default_folio_id)
    reservation_id = fields.Many2one(
        'pms.reservation',
        'Room',
        default=_default_reservation_id)
    service_line_ids = fields.One2many(
        'pms.service.line',
        'service_id')
    company_id = fields.Many2one(
        related='folio_id.company_id',
        string='Company',
        store=True,
        readonly=True)
    pms_property_id = fields.Many2one(
        'pms.property',
        store=True,
        readonly=True,
        related='folio_id.pms_property_id')
    tax_ids = fields.Many2many(
        'account.tax',
        string='Taxes',
        domain=['|', ('active', '=', False), ('active', '=', True)])
    move_line_ids = fields.Many2many(
        'account.move.line',
        'service_line_move_rel',
        'service_id',
        'move_line_id',
        string='move Lines',
        copy=False)
    analytic_tag_ids = fields.Many2many(
        'account.analytic.tag',
        string='Analytic Tags')
    currency_id = fields.Many2one(
        related='folio_id.currency_id',
        store=True,
        string='Currency',
        readonly=True)
    sequence = fields.Integer(string='Sequence', default=10)
    state = fields.Selection(related='folio_id.state')
    per_day = fields.Boolean(related='product_id.per_day', related_sudo=True)
    product_qty = fields.Integer('Quantity', default=1)
    days_qty = fields.Integer(compute="_compute_days_qty", store=True)
    is_board_service = fields.Boolean()
    to_print = fields.Boolean('Print', help='Print in Folio Report')
    # Non-stored related field to allow portal user to
    # see the image of the product he has ordered
    product_image = fields.Binary(
        'Product Image', related="product_id.image_1024",
        store=False, related_sudo=True)
    invoice_status = fields.Selection([
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')],
                                      string='Invoice Status',
                                      compute='_compute_invoice_status',
                                      store=True,
                                      readonly=True,
                                      default='no')
    channel_type = fields.Selection([
        ('door', 'Door'),
        ('mail', 'Mail'),
        ('phone', 'Phone'),
        ('call', 'Call Center'),
        ('web', 'Web')],
                                    string='Sales Channel')
    price_unit = fields.Float(
        'Unit Price',
        required=True,
        digits=dp.get_precision('Product Price'), default=0.0)
    discount = fields.Float(
        string='Discount (%)',
        digits=dp.get_precision('Discount'), default=0.0)
    qty_to_invoice = fields.Float(
        compute='_get_to_invoice_qty',
        string='To Invoice',
        store=True,
        readonly=True,
        digits=dp.get_precision('Product Unit of Measure'))
    qty_invoiced = fields.Float(
        compute='_get_invoice_qty',
        string='Invoiced',
        store=True,
        readonly=True,
        digits=dp.get_precision('Product Unit of Measure'))
    price_subtotal = fields.Monetary(
        string='Subtotal',
        readonly=True,
        store=True,
        compute='_compute_amount_service')
    price_total = fields.Monetary(
        string='Total',
        readonly=True,
        store=True,
        compute='_compute_amount_service')
    price_tax = fields.Float(
        string='Taxes',
        readonly=True,
        store=True,
        compute='_compute_amount_service')

    # Compute and Search methods
    @api.depends('qty_invoiced', 'product_qty', 'folio_id.state')
    def _get_to_invoice_qty(self):
        """
        Compute the quantity to invoice. If the invoice policy is order,
        the quantity to invoice is calculated from the ordered quantity.
        Otherwise, the quantity delivered is used.
        """
        for line in self:
            if line.folio_id.state not in ['draft']:
                line.qty_to_invoice = line.product_qty - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    @api.depends('move_line_ids.move_id.state',
                 'move_line_ids.quantity')
    def _get_invoice_qty(self):
        """
        Compute the quantity invoiced. If case of a refund,
        the quantity invoiced is decreased. Note that this is the case only
        if the refund is generated from the Folio and that is intentional: if
        a refund made would automatically decrease the invoiced quantity,
        then there is a risk of reinvoicing it automatically, which may
        not be wanted at all. That's why the refund has to be
        created from the Folio
        """
        for line in self:
            qty_invoiced = 0.0
            for invoice_line in line.move_line_ids:
                if invoice_line.move_id.state != 'cancel':
                    if invoice_line.move_id.type == 'out_invoice':
                        qty_invoiced += invoice_line.uom_id._compute_quantity(
                            invoice_line.quantity, line.product_id.uom_id)
                    elif invoice_line.move_id.type == 'out_refund':
                        qty_invoiced -= move_line.uom_id._compute_quantity(
                            invoice_line.quantity, line.product_id.uom_id)
            line.qty_invoiced = qty_invoiced

    @api.depends('product_qty', 'qty_to_invoice', 'qty_invoiced')
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a SO line. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done',
          we consider that there is nothing to invoice.
          This is also hte default value if the conditions of no other
          status is met.
        - to invoice: we refer to the quantity to invoice of the line.
          Refer to method `_get_to_invoice_qty()` for more information on
          how this quantity is calculated.
        - upselling: this is possible only for a product invoiced on ordered
          quantities for which we delivered more than expected.
          The could arise if, for example, a project took more time than
          expected but we decided not to invoice the extra cost to the
          client. This occurs onyl in state 'sale', so that when a Folio
          is set to done, the upselling opportunity is removed from the list.
        - invoiced: the quantity invoiced is larger or equal to the
          quantity ordered.
        """
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        for line in self:
            if line.folio_id.state in ('draft'):
                line.invoice_status = 'no'
            elif not float_is_zero(line.qty_to_invoice,
                                   precision_digits=precision):
                line.invoice_status = 'to invoice'
            elif float_compare(line.qty_invoiced, line.product_qty,
                               precision_digits=precision) >= 0:
                line.invoice_status = 'invoiced'
            else:
                line.invoice_status = 'no'

    @api.depends('product_qty', 'discount', 'price_unit', 'tax_ids')
    def _compute_amount_service(self):
        """
        Compute the amounts of the service line.
        """
        for record in self:
            folio = record.folio_id or self.env['pms.folio'].browse(
                self.env.context.get('default_folio_id'))
            reservation = record.reservation_id or self.env.context.get(
                'reservation_id')
            currency = folio.currency_id if folio else reservation.currency_id
            product = record.product_id
            price = record.price_unit * (1 - (record.discount or 0.0) * 0.01)
            taxes = record.tax_ids.compute_all(
                price, currency, record.product_qty, product=product)

            record.update({
                'price_tax': sum(t.get('amount', 0.0) for t in
                                 taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.depends('service_line_ids.day_qty')
    def _compute_days_qty(self):
        for record in self:
            if record.per_day:
                qty = sum(record.service_line_ids.mapped('day_qty'))
                vals = {
                    'days_qty': qty,
                    'product_qty': qty
                }
            else:
                vals = {'days_qty': 0}
            record.update(vals)

    # Constraints and onchanges
    @api.onchange('product_id')
    def onchange_product_id(self):
        """
        Compute the default quantity according to the
        configuration of the selected product, in per_day
        product configuration, the qty is autocalculated and
        readonly based on service_ids qty
        """
        if not self.product_id:
            return
        vals = {}
        vals['product_qty'] = 1.0
        for record in self:
            if record.per_day and record.reservation_id:
                product = record.product_id
                if self.env.context.get('default_reservation_id'):
                    reservation = self.env['pms.reservation'].browse(
                        self.env.context.get('default_reservation_id')
                    )
                else:
                    reservation = record.reservation_id
                if reservation.splitted:
                    checkin = reservation.real_checkin
                    checkout = reservation.real_checkout
                else:
                    checkin = reservation.checkin
                    checkout = reservation.checkout
                checkin_dt = fields.Date.from_string(checkin)
                checkout_dt = fields.Date.from_string(checkout)
                nights = abs((checkout_dt - checkin_dt).days)
                vals.update(record.prepare_service_ids(
                    dfrom=checkin,
                    days=nights,
                    per_person=product.per_person,
                    persons=reservation.adults,
                    old_line_days=record.service_line_ids,
                    consumed_on=product.consumed_on,
                ))
                if record.product_id.daily_limit > 0:
                    for day in record.service_line_ids:
                        day.no_free_resources()
        """
        Description and warnings
        """
        product = self.product_id.with_context(
            lang=self.folio_id.partner_id.lang,
            partner=self.folio_id.partner_id.id
        )
        title = False
        message = False
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s") % product.name
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False
                return result

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        vals['name'] = name
        """
        Compute tax and price unit
        """
        self._compute_tax_ids()
        vals['price_unit'] = self._compute_price_unit()
        record.update(vals)

    # Action methods
    
    def open_service_ids(self):
        action = self.env.ref('pms.action_pms_services_form').read()[0]
        action['views'] = [
            (self.env.ref('pms.pms_service_view_form').id, 'form')]
        action['res_id'] = self.id
        action['target'] = 'new'
        return action

    # ORM Overrides
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if not(name == '' and operator == 'ilike'):
            args += [
                '|',
                ('reservation_id.name', operator, name),
                ('name', operator, name)
            ]
        return super(PmsService, self).name_search(
            name='', args=args, operator='ilike', limit=limit)

    @api.model
    def create(self, vals):
        vals.update(self._prepare_add_missing_fields(vals))
        if self.compute_lines_out_vals(vals):
            reservation = self.env['pms.reservation'].browse(
                vals['reservation_id'])
            product = self.env['product.product'].browse(vals['product_id'])
            if reservation.splitted:
                checkin = reservation.real_checkin
                checkout = reservation.real_checkout
            else:
                checkin = reservation.checkin
                checkout = reservation.checkout
            checkin_dt = fields.Date.from_string(checkin)
            checkout_dt = fields.Date.from_string(checkout)
            nights = abs((checkout_dt - checkin_dt).days)
            vals.update(self.prepare_service_ids(
                dfrom=checkin,
                days=nights,
                per_person=product.per_person,
                persons=reservation.adults,
                old_day_lines=False,
                consumed_on=product.consumed_on,
            ))
        record = super(PmsService, self).create(vals)
        return record

    
    def write(self, vals):
        # If you write product, We must check if its necesary create or delete
        # service lines
        if vals.get('product_id'):
            product = self.env['product.product'].browse(
                vals.get('product_id'))
            if not product.per_day:
                vals.update({
                    'service_line_ids': [(5, 0, 0)]
                })
            else:
                for record in self:
                    reservations = self.env['pms.reservation']
                    reservation = reservations.browse(vals['reservation_id']) \
                        if 'reservation_id' in vals else record.reservation_id
                    if reservation.splitted:
                        checkin = reservation.real_checkin
                        checkout = reservation.real_checkout
                    else:
                        checkin = reservation.checkin
                        checkout = reservation.checkout
                    checkin_dt = fields.Date.from_string(checkin)
                    checkout_dt = fields.Date.from_string(checkout)
                    nights = abs((checkout_dt - checkin_dt).days)
                    record.update(record.prepare_service_ids(
                        dfrom=checkin,
                        days=nights,
                        per_person=product.per_person,
                        persons=reservation.adults,
                        old_line_days=self.service_line_ids,
                        consumed_on=product.consumed_on,
                    ))
        res = super(PmsService, self).write(vals)
        return res

    # Business methods
    @api.model
    def _prepare_add_missing_fields(self, values):
        """ Deduce missing required fields from the onchange """
        res = {}
        onchange_fields = ['price_unit', 'tax_ids', 'name']
        if values.get('product_id'):
            line = self.new(values)
            if any(f not in values for f in onchange_fields):
                line.onchange_product_id()
            for field in onchange_fields:
                if field not in values:
                    res[field] = line._fields[field].convert_to_write(
                        line[field], line)
        return res

    
    def compute_lines_out_vals(self, vals):
        """
        Compute if It is necesary service days in write/create
        """
        if not vals:
            vals = {}
        if 'product_id' in vals:
            product = self.env['product.product'].browse(vals['product_id']) \
                if 'product_id' in vals else self.product_id
            if (product.per_day and 'service_line_ids' not in vals):
                return True
        return False

    
    def _compute_tax_ids(self):
        for record in self:
            # If company_id is set, always filter taxes by the company
            folio = record.folio_id or self.env['pms.folio'].browse(
                self.env.context.get('default_folio_id'))
            reservation = record.reservation_id or self.env.context.get(
                'reservation_id')
            origin = folio if folio else reservation
            record.tax_ids = record.product_id.taxes_id.filtered(
                lambda r: not record.company_id or
                r.company_id == origin.company_id)

    
    def _get_display_price(self, product):
        folio = self.folio_id or self.env.context.get('default_folio_id')
        reservation = self.reservation_id or self.env.context.get(
            'reservation_id')
        origin = folio if folio else reservation
        if origin.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=origin.pricelist_id.id).price
        product_context = dict(
            self.env.context,
            partner_id=origin.partner_id.id,
            date=folio.date_order if folio else fields.Date.today(),
            uom=self.product_id.uom_id.id)
        final_price, rule_id = origin.pricelist_id.with_context(
            product_context).get_product_price_rule(
                self.product_id,
                self.product_qty or 1.0,
                origin.partner_id)
        base_price, currency_id = self.with_context(
            product_context)._get_real_price_currency(
                product,
                rule_id,
                self.product_qty,
                self.product_id.uom_id,
                origin.pricelist_id.id)
        if currency_id != origin.pricelist_id.currency_id.id:
            base_price = self.env['res.currency'].browse(
                currency_id).with_context(product_context).compute(
                    base_price,
                    origin.pricelist_id.currency_id)
        # negative discounts (= surcharge) are included in the display price
        return max(base_price, final_price)

    
    def _compute_price_unit(self):
        self.ensure_one()
        folio = self.folio_id or self.env.context.get('default_folio_id')
        reservation = self.reservation_id or self.env.context.get(
            'reservation_id')
        origin = reservation if reservation else folio
        if origin:
            partner = origin.partner_id
            pricelist = origin.pricelist_id
            if reservation and self.is_board_service:
                board_room_type = reservation.board_service_room_id
                if board_room_type.price_type == 'fixed':
                    return self.env['pms.board.service.room.type.line'].\
                        search([
                            ('pms_board_service_room_type_id',
                             '=', board_room_type.id),
                            ('product_id', '=', self.product_id.id)]).amount
                else:
                    return (reservation.price_total *
                            self.env['pms.board.service.room.type.line'].
                            search([
                                ('pms_board_service_room_type_id',
                                 '=', board_room_type.id),
                                ('product_id', '=', self.product_id.id)])
                            .amount) / 100
            else:
                product = self.product_id.with_context(
                    lang=partner.lang,
                    partner=partner.id,
                    quantity=self.product_qty,
                    date=folio.date_order if folio else fields.Date.today(),
                    pricelist=pricelist.id,
                    uom=self.product_id.uom_id.id,
                    fiscal_position=False
                )
                return self.env['account.tax']._fix_tax_included_price_company(
                    self._get_display_price(product),
                    product.taxes_id, self.tax_ids,
                    origin.company_id)

    @api.model
    def prepare_service_ids(self, **kwargs):
        """
        Prepare line and respect the old manual changes on lines
        """
        cmds = [(5, 0, 0)]
        old_line_days = kwargs.get('old_line_days')
        consumed_on = kwargs.get('consumed_on') if kwargs.get(
            'consumed_on') else 'before'
        total_qty = 0
        day_qty = 1
        # WARNING: Change adults in reservation NOT update qty service!!
        if kwargs.get('per_person'):
            day_qty = kwargs.get('persons')
        for i in range(0, kwargs.get('days')):
            if consumed_on == 'after':
                i += 1
            idate = (fields.Date.from_string(kwargs.get('dfrom')) +
                     timedelta(days=i)).strftime(
                         DEFAULT_SERVER_DATE_FORMAT)
            if not old_line_days or idate not in old_line_days.mapped('date'):
                cmds.append((0, False, {
                    'date': idate,
                    'day_qty': day_qty
                }))
                total_qty = total_qty + day_qty
            else:
                old_line = old_line_days.filtered(lambda r: r.date == idate)
                cmds.append((4, old_line.id))
                total_qty = total_qty + old_line.day_qty
        return {'service_line_ids': cmds, 'product_qty': total_qty}
