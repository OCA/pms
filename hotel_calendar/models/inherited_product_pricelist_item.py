# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    @api.model
    def create(self, vals):
        res = super(ProductPricelistItem, self).create(vals)
        pricelist_parity_id = self.env['ir.default'].sudo().get(
            'hotel.config.settings', 'parity_pricelist_id')
        if pricelist_parity_id:
            pricelist_parity_id = int(pricelist_parity_id)
        pricelist_id = res.pricelist_id.id
        product_tmpl_id = res.product_tmpl_id.id
        date_start = res.date_start
        vroom = self.env['hotel.virtual.room'].search([
            ('product_id.product_tmpl_id', '=', product_tmpl_id)
        ], limit=1)
        if pricelist_id == pricelist_parity_id and vroom:
            prod = vroom.product_id.with_context(
                quantity=1,
                date=date_start,
                pricelist=pricelist_id)
            prod_price = prod.price

            self.env['bus.hotel.calendar'].send_pricelist_notification({
                'pricelist_id': pricelist_id,
                'date': date_start,
                'virtual_room_id': vroom.id,
                'price': prod_price,
                'id': self.id,
            })

            vroom_pr_cached_obj = self.env['virtual.room.pricelist.cached']
            vroom_pr_cached_id = vroom_pr_cached_obj.search([
                ('virtual_room_id', '=', vroom.id),
                ('date', '=', date_start),
            ], limit=1)
            if vroom_pr_cached_id:
                vroom_pr_cached_id.write({'price': prod_price})
            else:
                vroom_pr_cached_obj.create({
                    'virtual_room_id': vroom.id,
                    'date': date_start,
                    'price': prod_price,
                })
        return res

    @api.multi
    def write(self, vals):
        pricelist_parity_id = self.env['ir.default'].sudo().get(
            'hotel.config.settings', 'parity_pricelist_id')
        if pricelist_parity_id:
            pricelist_parity_id = int(pricelist_parity_id)
        ret_vals = super(ProductPricelistItem, self).write(vals)

        vroom_pr_cached_obj = self.env['virtual.room.pricelist.cached']
        bus_calendar_obj = self.env['bus.hotel.calendar']
        vroom_obj = self.env['hotel.virtual.room']
        if vals.get('fixed_price'):
            for record in self:
                pricelist_id = vals.get('pricelist_id') or \
                    record.pricelist_id.id
                if pricelist_id != pricelist_parity_id:
                    continue
                date_start = vals.get('date_start') or record.date_start
                product_tmpl_id = vals.get('product_tmpl_id') or \
                    record.product_tmpl_id.id
                vroom = vroom_obj.search([
                    ('product_id.product_tmpl_id', '=', product_tmpl_id)
                ], limit=1)

                if vroom and date_start:
                    prod = vroom.product_id.with_context(
                        quantity=1,
                        date=date_start,
                        pricelist=pricelist_id)
                    prod_price = prod.price

                    bus_calendar_obj.send_pricelist_notification({
                        'pricelist_id': pricelist_id,
                        'date': date_start,
                        'virtual_room_id': vroom.id,
                        'price': prod_price,
                        'id': record.id,
                    })

                    vroom_pr_cached_id = vroom_pr_cached_obj.search([
                        ('virtual_room_id', '=', vroom.id),
                        ('date', '=', date_start),
                    ], limit=1)
                    if vroom_pr_cached_id:
                        vroom_pr_cached_id.write({'price': prod_price})
                    else:
                        vroom_pr_cached_obj.create({
                            'virtual_room_id': vroom.id,
                            'date': date_start,
                            'price': prod_price,
                        })
        return ret_vals

    @api.multi
    def unlink(self):
        pricelist_parity_id = self.env['ir.default'].sudo().get(
            'hotel.config.settings', 'parity_pricelist_id')
        if pricelist_parity_id:
            pricelist_parity_id = int(pricelist_parity_id)
        # Construct dictionary with relevant info of removed records
        unlink_vals = []
        for record in self:
            if record.pricelist_id.id != pricelist_parity_id:
                continue
            vroom = self.env['hotel.virtual.room'].search([
                ('product_id.product_tmpl_id', '=', record.product_tmpl_id.id)
            ], limit=1)
            unlink_vals.append({
                'pricelist_id': record.pricelist_id.id,
                'date': record.date_start,
                'vroom': vroom,
                'id': record.id,
            })
        # Do Normal Stuff
        res = super(ProductPricelistItem, self).unlink()
        # Do extra operations
        vroom_pr_cached_obj = self.env['virtual.room.pricelist.cached']
        bus_calendar_obj = self.env['bus.hotel.calendar']
        for vals in unlink_vals:
            pricelist_id = vals['pricelist_id']
            date_start = vals['date']
            vroom = vals['vroom']
            prod = vroom.product_id.with_context(
                quantity=1,
                date=date_start,
                pricelist=pricelist_id)

            # Send Notification to update calendar pricelist
            bus_calendar_obj.send_pricelist_notification({
                'pricelist_id': pricelist_id,
                'date': date_start,
                'virtual_room_id': vroom.id,
                'price': prod.price,
                'id': vals['id'],
            })

            # Remove records from cache model
            vroom_pr_cached_id = vroom_pr_cached_obj.search([
                ('virtual_room_id', '=', vroom.id),
                ('date', '=', date_start),
            ], limit=1)
            if vroom_pr_cached_id:
                vroom_pr_cached_id.unlink()
        return res
