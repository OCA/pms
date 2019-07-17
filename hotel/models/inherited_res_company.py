# Copyright 2017  Alexandre Díaz
# Copyright 2017  Dario Lodeiros
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    hotel_ids = fields.One2many('hotel.property', 'company_id', 'Hotels')

    additional_hours = fields.Integer('Additional Hours',
                                      help="Provide the min hours value for \
                                        check in, checkout days, whatever \
                                        the hours will be provided here based \
                                        on that extra days will be \
                                        calculated.")
    default_cancel_policy_days = fields.Integer('Cancelation Days')
    default_cancel_policy_percent = fields.Integer('Percent to pay')
    cardex_warning = fields.Text(
        'Warning in Cardex',
        default="Time to access rooms: 14: 00h. Departure time: \
                     12: 00h. If the accommodation is not left at that time, \
                     the establishment will charge a day's stay according to \
                     current rate that day",
        help="Notice under the signature on the traveler's ticket.")
