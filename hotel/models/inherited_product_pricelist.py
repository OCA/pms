# Copyright 2017  Alexandre Díaz
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductPricelist(models.Model):
    """ Before creating a 'daily' pricelist, you need to consider the following:
    A pricelist marked as daily is used as a daily rate plan for room types and
    therefore is related only with one hotel.
    """
    _inherit = 'product.pricelist'

    # Fields declaration
    hotel_ids = fields.Many2many('hotel.property', string='Hotels', required=False,
                                 ondelete='restrict')
    cancelation_rule_id = fields.Many2one('hotel.cancelation.rule',string="Cancelation Policy")

    pricelist_type = fields.Selection([
        ('daily', 'Daily Plan'),
    ], string='Pricelist Type', default='daily')
    is_staff = fields.Boolean('Is Staff')

    # Constraints and onchanges
    @api.constrains('pricelist_type', 'hotel_ids')
    def _check_pricelist_type_hotel_ids(self):
        for record in self:
            if record.pricelist_type == 'daily' and len(record.hotel_ids) != 1:
                raise ValidationError(_("A daily pricelist is used as a daily Rate Plan for room types "
                                        "and therefore must be related with one and only one hotel."))
            if record.pricelist_type == 'daily' and len(record.hotel_ids) == 1 \
                    and record.hotel_ids.id != record.hotel_ids.default_pricelist_id.hotel_ids.id:
                raise ValidationError(_("Relationship mismatch.") + " " +
                                      _("This pricelist is used as default in a different hotel."))
