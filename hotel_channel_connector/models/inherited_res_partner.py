# Copyright 2018 Alexandre Díaz <dev@redneboa.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class ResPartner(models.Model):

    _inherit = 'res.partner'

    unconfirmed = fields.Boolean('Unconfirmed', default=False)

    @api.multi
    def write(self, vals):
        res = False
        new_vat = vals.get('vat')
        if new_vat:
            org_partner_id = self.env['res.partner'].search([
                ('vat', '=', new_vat),
                ('unconfirmed', '=', False)
            ], limit=1)
            if org_partner_id:
                res = super(ResPartner, self).write(vals)
                for record in self:
                    # replace all folios partners with the
                    # first 'confirmed' partner with the same vat
                    if record.unconfirmed:
                        folio_ids = self.env['hotel.folio'].search([
                            ('partner_id', '=', record.id)
                        ])
                        if folio_ids:
                            folio_ids.write({
                                'partner_id': org_partner_id.id,
                            })
                        folio_ids = self.env['hotel.folio'].search([
                            ('partner_invoice_id', '=', record.id)
                        ])
                        if folio_ids:
                            folio_ids.write({
                                'partner_invoice_id': org_partner_id.id,
                            })
                        record.write({'active': False})
            else:
                # If not found, this is the 'confirmed'
                vals.update({'unconfirmed': False})
                res = super(ResPartner, self).write(vals)
        else:
            # If not have new vat... do nothing
            res = super(ResPartner, self).write(vals)

        return res
