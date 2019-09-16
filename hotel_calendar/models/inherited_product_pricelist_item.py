# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    # CRUD methods
    @api.model
    def create(self, vals):
        res = super(ProductPricelistItem, self).create(vals)
        # TODO: refactoring res.config.settings', 'default_pricelist_id' by the current hotel.property.pricelist_id
        pricelist_default_id = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_pricelist_id')
        if pricelist_default_id:
            pricelist_default_id = int(pricelist_default_id)
        pricelist_id = res.pricelist_id.id
        product_tmpl_id = res.product_tmpl_id.id
        date_start = res.date_start
        room_type = self.env['hotel.room.type'].search([
            ('product_id.product_tmpl_id', '=', product_tmpl_id)
        ], limit=1)
        if pricelist_id == pricelist_default_id and room_type:
            prod = room_type.product_id.with_context(
                quantity=1,
                date=date_start,
                pricelist=pricelist_id)
            prod_price = prod.price

            self.env['bus.hotel.calendar'].send_pricelist_notification({
                'pricelist_id': pricelist_id,
                'date': date_start,
                'room_id': room_type.id,
                'price': prod_price,
                'id': self.id,
            })
        return res

    @api.multi
    def write(self, vals):
        # TODO: refactoring res.config.settings', 'default_pricelist_id' by the current hotel.property.pricelist_id
        pricelist_default_id = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_pricelist_id')
        if pricelist_default_id:
            pricelist_default_id = int(pricelist_default_id)
        ret_vals = super(ProductPricelistItem, self).write(vals)

        bus_calendar_obj = self.env['bus.hotel.calendar']
        room_type_obj = self.env['hotel.room.type']
        if vals.get('fixed_price'):
            for record in self:
                pricelist_id = vals.get('pricelist_id') or \
                    record.pricelist_id.id
                if pricelist_id != pricelist_default_id:
                    continue
                date_start = vals.get('date_start') or record.date_start
                product_tmpl_id = vals.get('product_tmpl_id') or \
                    record.product_tmpl_id.id
                room_type = room_type_obj.search([
                    ('product_id.product_tmpl_id', '=', product_tmpl_id)
                ], limit=1)

                if room_type and date_start:
                    prod = room_type.product_id.with_context(
                        quantity=1,
                        date=date_start,
                        pricelist=pricelist_id)
                    prod_price = prod.price

                    bus_calendar_obj.send_pricelist_notification({
                        'pricelist_id': pricelist_id,
                        'date': date_start,
                        'room_id': room_type.id,
                        'price': prod_price,
                        'id': record.id,
                    })
        return ret_vals

    @api.multi
    def unlink(self):
        # TODO: refactoring res.config.settings', 'default_pricelist_id' by the current hotel.property.pricelist_id
        pricelist_default_id = self.env['ir.default'].sudo().get(
            'res.config.settings', 'default_pricelist_id')
        if pricelist_default_id:
            pricelist_default_id = int(pricelist_default_id)
        # Construct dictionary with relevant info of removed records
        unlink_vals = []
        for record in self:
            if record.pricelist_id.id != pricelist_default_id:
                continue
            room_type = self.env['hotel.room.type'].search([
                ('product_id.product_tmpl_id', '=', record.product_tmpl_id.id)
            ], limit=1)
            unlink_vals.append({
                'pricelist_id': record.pricelist_id.id,
                'date': record.date_start,
                'room': room_type,
                'id': record.id,
            })
        # Do Normal Stuff
        res = super(ProductPricelistItem, self).unlink()
        # Do extra operations
        bus_calendar_obj = self.env['bus.hotel.calendar']
        for vals in unlink_vals:
            pricelist_id = vals['pricelist_id']
            date_start = vals['date']
            room_type = vals['room']
            prod = room_type.product_id.with_context(
                quantity=1,
                date=date_start,
                pricelist=pricelist_id)

            # Send Notification to update calendar pricelist
            bus_calendar_obj.send_pricelist_notification({
                'pricelist_id': pricelist_id,
                'date': date_start,
                'room_id': room_type.id,
                'price': prod.price,
                'id': vals['id'],
            })
        return res
