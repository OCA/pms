# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime, timedelta
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class ReservationRestriction(models.Model):
    _inherit = 'hotel.virtual.room.restriction'

    wpid = fields.Char("WuBook Restriction Plan ID", readonly=True)
    wdaily = fields.Boolean("Plan Daily", default=True, readonly=True)

    @api.multi
    def get_wubook_restrictions(self):
        self.ensure_one()
        prices = {}
        min_date = False
        max_date = False
        for item in self.item_ids:
            if not item.date_start or not item.date_end:
                continue
            date_start_dt = fields.Datetime.from_string(item.date_start)
            date_end_dt = fields.Datetime.from_string(item.date_end)
            if not min_date or date_start_dt < min_date:
                min_date = date_start_dt
            if not max_date or date_end_dt > max_date:
                max_date = date_end_dt
        if not min_date or not max_date:
            return prices
        days_diff = abs((max_date - min_date).days)
        vrooms = self.env['hotel.room.type'].search([
            ('wrid', '!=', ''),
            ('wrid', '!=', False)
        ])
        for vroom in vrooms:
            prices.update({vroom.wrid: []})
            for i in range(0, days_diff or 1):
                ndate_dt = min_date + timedelta(days=i)
                product_id = vroom.product_id.with_context(
                    quantity=1,
                    date=ndate_dt.strftime(DEFAULT_SERVER_DATE_FORMAT),
                    pricelist=self.id,
                    uom=vroom.product_id.product_tmpl_id.uom_id.id)
                prices[vroom.wrid].append(product_id.price)
        return prices

    @api.model
    def create(self, vals):
        if self._context.get('wubook_action', True) and \
                self.env['wubook'].is_valid_account():
            wpid = self.env['wubook'].create_rplan(vals['name'])
            if not wpid:
                raise ValidationError(_("Can't create restriction plan on \
                                WuBook"))
            vals.update({'wpid': wpid})

        rules = self._context.get('rules')
        if rules:
            vals.update({'wdaily': False})

        restriction = super(ReservationRestriction, self).create(vals)

        if rules:
            # Basic Rules
            vroom_rest_it_obj = self.env['hotel.virtual.room.restriction.item']
            vroom_rest_it_obj.with_context({'wubook_action': False}).create({
                'closed_arrival': rules['closed_arrival'],
                'closed': rules['closed'],
                'min_stay': rules['min_stay'],
                'closed_departure': rules['closed_departure'],
                'max_stay': rules['max_stay'],
                'min_stay_arrival': rules['min_stay_arrival'],
                'restriction_id': restriction.id,
                'applied_on': '1_global',
            })

        return restriction

    @api.multi
    def write(self, vals):
        nname = vals.get('name')
        if self._context.get('wubook_action', True) and nname and \
                self.env['wubook'].is_valid_account():
            for record in self:
                if record.wpid and record.wpid != '':
                    wres = self.env['wubook'].rename_rplan(
                        vals.get('wpid', record.wpid),
                        nname)
                    if not wres:
                        raise ValidationError(_("Can't rename restriction plan \
                        on WuBook"))
        updated = super(ReservationRestriction, self).write(vals)
        return updated

    @api.multi
    def unlink(self):
        if self._context.get('wubook_action', True) and \
                self.env['wubook'].is_valid_account():
            for record in self:
                if record.wpid and record.wpid != '':
                    wres = self.env['wubook'].delete_rplan(record.wpid)
                    if not wres:
                        raise ValidationError(_("Can't delete restriction plan \
                        on WuBook"))
        return super(ReservationRestriction, self).unlink()

    @api.multi
    def import_restriction_plans(self):
        return self.env['wubook'].import_restriction_plans()

    @api.multi
    @api.depends('name')
    def name_get(self):
        roomRestrictionObj = self.env['hotel.virtual.room.restriction']
        org_names = super(ReservationRestriction, self).name_get()
        names = []
        for name in org_names:
            restriction_id = roomRestrictionObj.browse(name[0])
            if restriction_id.wpid:
                names.append((name[0], '%s (WuBook)' % name[1]))
            else:
                names.append((name[0], name[1]))
        return names
