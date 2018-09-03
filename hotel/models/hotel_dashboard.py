# Copyright 2018  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
from datetime import datetime, timedelta
from babel.dates import format_datetime, format_date
from odoo import models, api, _, fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools.misc import formatLang

class HotelDashboard(models.Model):
    _name = "hotel.dashboard"

    # FIXME
    def _get_count(self):
        resevations_count = self.env['hotel.reservation'].search_count(
            [('sate', '=', 'confirm')])
        folios_count = self.env['hotel.folio'].search_count(
            [('sate', '=', 'sales_order')])
        next_arrivals_count = self.env['hotel.reservation'].search_count(
            [('is_checkin', '=', True)])

        self.orders_count = len(orders_count)
        self.quotations_count = len(quotations_count)
        self.orders_done_count = len(orders_done_count)

    @api.one
    def _kanban_dashboard(self):
        if self.graph_type == 'bar':
            self.kanban_dashboard_graph = json.dumps(self.get_bar_graph_datas())
        elif self.graph_type == 'line':
            self.kanban_dashboard_graph = json.dumps(self.get_line_graph_datas())

    @api.one
    def _kanban_dashboard_graph(self):
        self.kanban_dashboard_graph = json.dumps(self.get_bar_graph_datas())
        #~ if (self.type in ['sale', 'purchase']):
            #~ self.kanban_dashboard_graph = json.dumps(self.get_bar_graph_datas())
        #~ elif (self.type in ['cash', 'bank']):
            #~ self.kanban_dashboard_graph = json.dumps(self.get_line_graph_datas())

    color = fields.Integer(string='Color Index')
    name = fields.Char(string="Name")
    type = fields.Char(default="sale")
    graph_type = fields.Selection([
        ('line', 'Line'),
        ('bar', 'Bar'),
        ('none', 'None')])
    reservations_count = fields.Integer(compute='_get_count')
    folios_count = fields.Integer(compute='_get_count')
    next_arrivals_count = fields.Integer(compute='_get_count')
    kanban_dashboard = fields.Text(compute='_kanban_dashboard')
    kanban_dashboard_graph = fields.Text(compute='_kanban_dashboard_graph')
    show_on_dashboard = fields.Boolean(
        string='Show journal on dashboard',
        help="Whether this journal should be displayed on the dashboard or not",
        default=True)

    @api.multi
    def get_bar_graph_datas(self):
        data = []
        today = datetime.strptime(fields.Date.context_today(self), DF)
        day_of_week = int(format_datetime(today, 'e', locale=self._context.get('lang') or 'en_US'))
        for i in range(0, 15):
            if i == 0:
                label = _('Today')
            else:
                label = format_date(today + timedelta(days=i),
                                    'd',
                                    locale=self._context.get('lang') or 'en_US')
            data.append({'label':label, 'value':0.0, 'type': 'past' if i < 0 else 'future'})
        # Build SQL query to find amount aggregated by week
        select_sql_clause = """SELECT count(id) as total from hotel_reservation where state != 'cancelled'"""
        query = "("+select_sql_clause+" and date(checkin) = '"+today.strftime(DF)+"')"
        for i in range(1,15):
            next_date = today + timedelta(days=i)
            query += " UNION ALL ("+select_sql_clause+" and date(checkin) = '"+next_date.strftime(DF)+"')"

        self.env.cr.execute(query)
        query_results = self.env.cr.dictfetchall()
        for index_k, index_v in enumerate(query_results):
            data[index_k]['value'] = index_v.get('total')
        return [{'values': data}]

    @api.multi
    def get_journal_dashboard_datas(self):
        #~ currency = self.currency_id or self.company_id.currency_id
        #~ number_to_reconcile = last_balance = account_sum = 0
        #~ ac_bnk_stmt = []
        #~ title = ''
        #~ number_draft = number_waiting = number_late = 0
        #~ sum_draft = sum_waiting = sum_late = 0.0
        #~ if self.type in ['bank', 'cash']:
            #~ last_bank_stmt = self.env['account.bank.statement'].search([('journal_id', 'in', self.ids)], order="date desc, id desc", limit=1)
            #~ last_balance = last_bank_stmt and last_bank_stmt[0].balance_end or 0
            #~ #Get the number of items to reconcile for that bank journal
            #~ self.env.cr.execute("""SELECT COUNT(DISTINCT(statement_line_id))
                        #~ FROM account_move where statement_line_id
                        #~ IN (SELECT line.id
                            #~ FROM account_bank_statement_line AS line
                            #~ LEFT JOIN account_bank_statement AS st
                            #~ ON line.statement_id = st.id
                            #~ WHERE st.journal_id IN %s and st.state = 'open')""", (tuple(self.ids),))
            #~ already_reconciled = self.env.cr.fetchone()[0]
            #~ self.env.cr.execute("""SELECT COUNT(line.id)
                            #~ FROM account_bank_statement_line AS line
                            #~ LEFT JOIN account_bank_statement AS st
                            #~ ON line.statement_id = st.id
                            #~ WHERE st.journal_id IN %s and st.state = 'open'""", (tuple(self.ids),))
            #~ all_lines = self.env.cr.fetchone()[0]
            #~ number_to_reconcile = all_lines - already_reconciled
            #~ # optimization to read sum of balance from account_move_line
            #~ account_ids = tuple(filter(None, [self.default_debit_account_id.id, self.default_credit_account_id.id]))
            #~ if account_ids:
                #~ amount_field = 'balance' if (not self.currency_id or self.currency_id == self.company_id.currency_id) else 'amount_currency'
                #~ query = """SELECT sum(%s) FROM account_move_line WHERE account_id in %%s AND date <= %%s;""" % (amount_field,)
                #~ self.env.cr.execute(query, (account_ids, fields.Date.today(),))
                #~ query_results = self.env.cr.dictfetchall()
                #~ if query_results and query_results[0].get('sum') != None:
                    #~ account_sum = query_results[0].get('sum')
        #~ #TODO need to check if all invoices are in the same currency than the journal!!!!
        #~ elif self.type in ['sale', 'purchase']:
            #~ title = _('Bills to pay') if self.type == 'purchase' else _('Invoices owed to you')
            #~ # optimization to find total and sum of invoice that are in draft, open state
            #~ query = """SELECT state, amount_total, currency_id AS currency, type FROM account_invoice WHERE journal_id = %s AND state NOT IN ('paid', 'cancel');"""
            #~ self.env.cr.execute(query, (self.id,))
            #~ query_results = self.env.cr.dictfetchall()
            #~ today = datetime.today()
            #~ query = """SELECT amount_total, currency_id AS currency, type FROM account_invoice WHERE journal_id = %s AND date < %s AND state = 'open';"""
            #~ self.env.cr.execute(query, (self.id, today))
            #~ late_query_results = self.env.cr.dictfetchall()
            #~ for result in query_results:
                #~ if result['type'] in ['in_refund', 'out_refund']:
                    #~ factor = -1
                #~ else:
                    #~ factor = 1
                #~ cur = self.env['res.currency'].browse(result.get('currency'))
                #~ if result.get('state') in ['draft', 'proforma', 'proforma2']:
                    #~ number_draft += 1
                    #~ sum_draft += cur.compute(result.get('amount_total'), currency) * factor
                #~ elif result.get('state') == 'open':
                    #~ number_waiting += 1
                    #~ sum_waiting += cur.compute(result.get('amount_total'), currency) * factor
            #~ for result in late_query_results:
                #~ if result['type'] in ['in_refund', 'out_refund']:
                    #~ factor = -1
                #~ else:
                    #~ factor = 1
                #~ cur = self.env['res.currency'].browse(result.get('currency'))
                #~ number_late += 1
                #~ sum_late += cur.compute(result.get('amount_total'), currency) * factor

        #~ difference = currency.round(last_balance-account_sum) + 0.0
        return {
            'graph': self.graph_type,
            'number_to_reconcile': 11,
            'account_balance': 4314,
            'last_balance': 252,
            'difference': 432,
            'number_draft': 32,
            'number_waiting': 44,
            'number_late': 23,
            'sum_draft': 2424245,
            'sum_waiting': 3124312,
            'sum_late': 23123,
            'currency_id': 1,
            'bank_statements_source': 'fonte',
            'title': 'titulo',
        }

    @api.multi
    def get_line_graph_datas(self):
        data = []
        today = datetime.strptime(fields.Date.context_today(self), DF)
        days=30

        for i in range(-1, days + 1):
            ndate = today + timedelta(days=i)
            ndate_str = ndate.strftime(DF)
            day_onboard = self.env['hotel.reservation.line'].search_count([('date','=',ndate)])
            locale = self._context.get('lang') or 'en_US'
            short_name = format_date(ndate, 'd', locale=locale)
            name = format_date(ndate, 'd LLLL Y', locale=locale)
            data.append({'x':short_name,'y':day_onboard, 'name':name})
        return [{'values': data, 'area': True}]

    @api.multi
    def action_create_new(self):
        #~ ctx = self._context.copy()
        #~ model = 'account.invoice'
        #~ if self.type == 'sale':
            #~ ctx.update({'journal_type': self.type, 'default_type': 'out_invoice', 'type': 'out_invoice', 'default_journal_id': self.id})
            #~ if ctx.get('refund'):
                #~ ctx.update({'default_type':'out_refund', 'type':'out_refund'})
            #~ view_id = self.env.ref('account.invoice_form').id
        #~ elif self.type == 'purchase':
            #~ ctx.update({'journal_type': self.type, 'default_type': 'in_invoice', 'type': 'in_invoice', 'default_journal_id': self.id})
            #~ if ctx.get('refund'):
                #~ ctx.update({'default_type': 'in_refund', 'type': 'in_refund'})
            #~ view_id = self.env.ref('account.invoice_supplier_form').id
        #~ else:
            #~ ctx.update({'default_journal_id': self.id})
            #~ view_id = self.env.ref('account.view_move_form').id
            #~ model = 'account.move'
        model = "hotel.folio"
        view_id = self.env.ref('hotel.view_hotel_folio1_form').id
        ctx=''
        return {
            'name': _('Create invoice/bill'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': model,
            'view_id': view_id,
            'context': ctx,
        }

    @api.multi
    def open_action(self):
        """return action based on type for related journals"""
        #~ action_name = self._context.get('action_name', False)
        #~ if not action_name:
            #~ if self.type == 'bank':
                #~ action_name = 'action_bank_statement_tree'
            #~ elif self.type == 'cash':
                #~ action_name = 'action_view_bank_statement_tree'
            #~ elif self.type == 'sale':
                #~ action_name = 'action_invoice_tree1'
            #~ elif self.type == 'purchase':
                #~ action_name = 'action_invoice_tree2'
            #~ else:
                #~ action_name = 'action_move_journal_line'

        #~ _journal_invoice_type_map = {
            #~ ('sale', None): 'out_invoice',
            #~ ('purchase', None): 'in_invoice',
            #~ ('sale', 'refund'): 'out_refund',
            #~ ('purchase', 'refund'): 'in_refund',
            #~ ('bank', None): 'bank',
            #~ ('cash', None): 'cash',
            #~ ('general', None): 'general',
        #~ }
        #~ invoice_type = _journal_invoice_type_map[(self.type, self._context.get('invoice_type'))]

        #~ ctx = self._context.copy()
        #~ ctx.pop('group_by', None)
        #~ ctx.update({
            #~ 'journal_type': self.type,
            #~ 'default_journal_id': self.id,
            #~ 'search_default_journal_id': self.id,
            #~ 'default_type': invoice_type,
            #~ 'type': invoice_type
        #~ })

        #~ [action] = self.env.ref('account.%s' % action_name).read()
        #~ action['context'] = ctx
        #~ action['domain'] = self._context.get('use_domain', [])
        #~ if action_name in ['action_bank_statement_tree', 'action_view_bank_statement_tree']:
            #~ action['views'] = False
            #~ action['view_id'] = False
        return False
